-- ============================================================
-- B站热门视频数据分析平台 · 数据库设计文档
-- 版本: v1.0
-- 日期: 2026-08-23
-- 数据库: MySQL 8.0+
-- 字符集: utf8mb4
-- ============================================================

-- ------------------------------------------------------------
-- 1. 创建数据库
-- ------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS bili_hot
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE bili_hot;

-- ============================================================
-- 2. 核心业务表设计
-- ============================================================

-- ------------------------------------------------------------
-- 2.1 用户表 (users)
-- 描述: 平台注册用户，支持普通用户和管理员两种角色
-- 来源: PRD 3.2.1 用户模块
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
    `id`            BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT  COMMENT '用户主键ID',
    `username`      VARCHAR(50)      NOT NULL                 COMMENT '用户名，用于登录',
    `email`         VARCHAR(100)     NOT NULL                 COMMENT '邮箱，用于注册验证和找回密码',
    `password_hash` VARCHAR(255)     NOT NULL                 COMMENT '密码哈希值，bcrypt加密',
    `avatar_url`    VARCHAR(500)     DEFAULT NULL             COMMENT '用户头像URL',
    `nickname`      VARCHAR(50)      DEFAULT NULL             COMMENT '用户昵称，展示用',
    `role`          ENUM('user','admin') NOT NULL DEFAULT 'user' COMMENT '用户角色: user-普通用户, admin-管理员',
    `is_active`     TINYINT(1)       NOT NULL DEFAULT 1       COMMENT '账号状态: 1-启用, 0-禁用',
    `email_verified` TINYINT(1)      NOT NULL DEFAULT 0       COMMENT '邮箱是否已验证: 1-已验证, 0-未验证',
    `last_login_at` DATETIME         DEFAULT NULL             COMMENT '最后登录时间',
    `created_at`    DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`    DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`),
    UNIQUE KEY `uk_email` (`email`),
    KEY `idx_role` (`role`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ------------------------------------------------------------
-- 2.2 UP主表 (up_users)
-- 描述: B站UP主信息，存储UP主的基本资料和统计数据
-- 来源: PRD 3.2.2 数据采集模块 - UP主相关字段
-- 数据来源API:
--   ③ UP主信息 API: /x/space/acc/info → 昵称、等级、性别、签名
--   ④ UP主统计 API: /x/relation/stat → 粉丝数、关注数
--   ⑤ UP主投稿 API: /x/space/upstat → 总播放量、总获赞数
--   ⑥ UP主视频列表 API: /x/space/arc/search → 总投稿视频数
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `up_users`;
CREATE TABLE `up_users` (
    `id`              BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT  COMMENT 'UP主记录主键ID',
    `up_uid`          BIGINT UNSIGNED  NOT NULL                 COMMENT 'B站UP主UID (mid)，B站唯一标识',
    `nickname`        VARCHAR(100)     NOT NULL                 COMMENT 'UP主昵称',
    `sex`             ENUM('男','女','保密') DEFAULT '保密'       COMMENT 'UP主性别',
    `level`           TINYINT UNSIGNED DEFAULT 0                COMMENT 'UP主等级，范围 Lv0-Lv6',
    `sign`            VARCHAR(500)     DEFAULT NULL             COMMENT 'UP主个人签名/简介',
    `avatar_url`      VARCHAR(500)     DEFAULT NULL             COMMENT 'UP主头像URL',
    `follower_count`  BIGINT UNSIGNED  NOT NULL DEFAULT 0       COMMENT '粉丝数',
    `following_count` BIGINT UNSIGNED  NOT NULL DEFAULT 0       COMMENT '关注数',
    `total_likes`     BIGINT UNSIGNED  NOT NULL DEFAULT 0       COMMENT '总获赞数',
    `total_plays`     BIGINT UNSIGNED  NOT NULL DEFAULT 0       COMMENT '总播放量',
    `video_count`     INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '总投稿视频数',
    `crawl_time`      DATETIME         NOT NULL                 COMMENT '本次数据采集时间',
    `created_at`      DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次录入时间',
    `updated_at`      DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最近更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_up_uid` (`up_uid`),
    KEY `idx_nickname` (`nickname`),
    KEY `idx_follower_count` (`follower_count`),
    KEY `idx_level` (`level`),
    KEY `idx_crawl_time` (`crawl_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='UP主信息表';

-- ------------------------------------------------------------
-- 2.3 视频表 (videos)
-- 描述: 热门视频最新快照数据，每个bvid只保留最新一条记录
-- 来源: PRD 3.2.2 数据采集模块 - 视频相关字段
-- 数据来源API:
--   ① 热门列表 API: /x/web-interface/popular → 视频基础数据 + UP主owner信息
-- 衍生字段: 互动率、热度评分 (PRD 3.2.3 / 3.2.4)
-- 注: 视频标签已拆分到独立表 video_tags (来自 ② 视频详情 API)
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `videos`;
CREATE TABLE `videos` (
    `id`              BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT  COMMENT '视频记录主键ID',
    `bvid`            VARCHAR(20)      NOT NULL                 COMMENT 'B站视频BV号，唯一标识一个视频',
    `title`           VARCHAR(500)     NOT NULL                 COMMENT '视频标题',
    `cover_url`       VARCHAR(500)     DEFAULT NULL             COMMENT '视频封面图URL',
    `description`     TEXT             DEFAULT NULL             COMMENT '视频简介/描述',
    -- 数据统计字段 (来自热门列表API stat对象)
    `play_count`      BIGINT UNSIGNED  NOT NULL DEFAULT 0       COMMENT '播放量',
    `danmaku_count`   INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '弹幕数',
    `comment_count`   INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '评论数',
    `like_count`      INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '点赞数',
    `coin_count`      INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '投币数',
    `favorite_count`  INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '收藏数',
    `share_count`     INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '转发数',
    -- 视频属性字段 (来自热门列表API)
    `duration`        INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '视频时长(秒)',
    `pub_time`        DATETIME         NOT NULL                 COMMENT '视频发布时间',
    `partition_main`  VARCHAR(50)      NOT NULL DEFAULT '未知'   COMMENT '一级分区名称，如"动画"、"游戏"',
    `partition_sub`   VARCHAR(50)      DEFAULT NULL             COMMENT '二级分区名称',
    -- 关联UP主
    `up_id`           BIGINT UNSIGNED  NOT NULL                 COMMENT '关联UP主记录ID，外键关联up_users.id',
    `up_uid`          BIGINT UNSIGNED  NOT NULL                 COMMENT 'B站UP主UID (冗余字段，方便查询)',
    -- 衍生计算字段 (PRD 3.2.3 / 3.2.4)
    `interaction_rate` DECIMAL(8,6)    DEFAULT NULL             COMMENT '互动率 = (点赞+评论+弹幕+投币+收藏+转发)/播放量',
    `heat_score`      DECIMAL(12,2)   DEFAULT NULL             COMMENT '综合热度评分 = 播放量×0.3 + 点赞×0.15 + 评论×0.15 + 弹幕×0.1 + 投币×0.1 + 收藏×0.1 + 转发×0.1',
    -- 采集与状态
    `crawl_time`      DATETIME         NOT NULL                 COMMENT '本次数据采集时间',
    `is_active`       TINYINT(1)       NOT NULL DEFAULT 1       COMMENT '数据状态: 1-正常, 0-异常/已排除',
    `created_at`      DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次录入时间',
    `updated_at`      DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最近更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_bvid` (`bvid`),
    KEY `idx_up_id` (`up_id`),
    KEY `idx_up_uid` (`up_uid`),
    KEY `idx_play_count` (`play_count`),
    KEY `idx_pub_time` (`pub_time`),
    KEY `idx_partition_main` (`partition_main`),
    KEY `idx_crawl_time` (`crawl_time`),
    KEY `idx_interaction_rate` (`interaction_rate`),
    KEY `idx_heat_score` (`heat_score`),
    KEY `idx_is_active` (`is_active`),
    KEY `idx_partition_pub` (`partition_main`, `pub_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='热门视频表(最新快照)';

-- ------------------------------------------------------------
-- 2.4 视频标签表 (video_tags)
-- 描述: 视频与标签的多对多关系，每个视频可以有多个标签
--       独立建表便于标签维度的数据分析（词云、热门标签趋势、标签共现等）
-- 来源: PRD 3.2.2 ② 视频详情 API / 3.2.4 标签词云
-- 数据来源API: /x/web-interface/view/detail → data.tags
-- 典型分析场景:
--   ① 标签频率统计 → 词云图
--   ② 按标签筛选视频 → 热门标签榜单
--   ③ 标签与分区交叉分析 → 分区标签偏好
--   ④ 标签与播放量关联 → 哪些标签的视频更受欢迎
--   ⑤ 标签共现分析 → 标签关联网络图
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `video_tags`;
CREATE TABLE `video_tags` (
    `id`          BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT  COMMENT '标签记录主键ID',
    `bvid`        VARCHAR(20)      NOT NULL                 COMMENT 'B站视频BV号，关联videos.bvid',
    `tag_name`    VARCHAR(100)     NOT NULL                 COMMENT '标签名称',
    `crawl_time`  DATETIME         NOT NULL                 COMMENT '本次标签采集时间',
    `created_at`  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_bvid_tag` (`bvid`, `tag_name`),
    KEY `idx_bvid` (`bvid`),
    KEY `idx_tag_name` (`tag_name`),
    KEY `idx_crawl_time` (`crawl_time`),
    KEY `idx_tag_crawl` (`tag_name`, `crawl_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='视频标签关联表';

-- ------------------------------------------------------------
-- 2.5 视频历史快照表 (video_snapshots)
-- 描述: 视频每日数据快照，用于趋势分析和历史对比
--       每次爬取将当日数据写入此表，一条bvid每天一条记录
-- 来源: PRD 3.2.4 时间趋势分析 / 5.1 数据流设计
-- 用途: 按小时/天聚合播放量，绘制折线图/面积图
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `video_snapshots`;
CREATE TABLE `video_snapshots` (
    `id`              BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT  COMMENT '快照记录主键ID',
    `bvid`            VARCHAR(20)      NOT NULL                 COMMENT 'B站视频BV号',
    `video_id`        BIGINT UNSIGNED  NOT NULL                 COMMENT '关联videos.id',
    `up_id`           BIGINT UNSIGNED  NOT NULL                 COMMENT '关联up_users.id',
    -- 当日统计数据
    `play_count`      BIGINT UNSIGNED  NOT NULL DEFAULT 0       COMMENT '当日播放量',
    `danmaku_count`   INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '当日弹幕数',
    `comment_count`   INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '当日评论数',
    `like_count`      INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '当日点赞数',
    `coin_count`      INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '当日投币数',
    `favorite_count`  INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '当日收藏数',
    `share_count`     INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '当日转发数',
    -- 增量数据 (相比上一快照的增量)
    `play_increment`        BIGINT   DEFAULT NULL              COMMENT '播放增量',
    `danmaku_increment`     INT      DEFAULT NULL              COMMENT '弹幕增量',
    `comment_increment`     INT      DEFAULT NULL              COMMENT '评论增量',
    `like_increment`        INT      DEFAULT NULL              COMMENT '点赞增量',
    `coin_increment`        INT      DEFAULT NULL              COMMENT '投币增量',
    `favorite_increment`    INT      DEFAULT NULL              COMMENT '收藏增量',
    `share_increment`       INT      DEFAULT NULL              COMMENT '转发增量',
    -- 衍生字段
    `interaction_rate` DECIMAL(8,6)    DEFAULT NULL             COMMENT '当日互动率',
    `heat_score`      DECIMAL(12,2)   DEFAULT NULL             COMMENT '当日综合热度评分',
    `rank_position`   INT UNSIGNED     DEFAULT NULL             COMMENT '当日热门榜排名',
    -- 快照信息
    `snapshot_date`   DATE             NOT NULL                 COMMENT '快照日期 (YYYY-MM-DD)',
    `snapshot_hour`   TINYINT UNSIGNED DEFAULT NULL             COMMENT '快照小时 (0-23)，按小时采集时使用',
    `crawl_time`      DATETIME         NOT NULL                 COMMENT '精确采集时间',
    `created_at`      DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_bvid_date_hour` (`bvid`, `snapshot_date`, `snapshot_hour`),
    KEY `idx_video_id` (`video_id`),
    KEY `idx_up_id` (`up_id`),
    KEY `idx_snapshot_date` (`snapshot_date`),
    KEY `idx_bvid_date` (`bvid`, `snapshot_date`),
    KEY `idx_heat_score` (`heat_score`),
    KEY `idx_rank_position` (`rank_position`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='视频每日数据快照表(历史趋势)';

-- ------------------------------------------------------------
-- 2.6 UP主历史快照表 (up_user_snapshots)
-- 描述: UP主每日数据快照，追踪UP主粉丝增长等趋势
-- 来源: PRD 3.2.4 UP主影响力分析
-- 用途: 粉丝增长曲线、UP主影响力变化趋势
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `up_user_snapshots`;
CREATE TABLE `up_user_snapshots` (
    `id`               BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT  COMMENT '快照记录主键ID',
    `up_id`            BIGINT UNSIGNED  NOT NULL                 COMMENT '关联up_users.id',
    `up_uid`           BIGINT UNSIGNED  NOT NULL                 COMMENT 'B站UP主UID',
    `follower_count`   BIGINT UNSIGNED  NOT NULL DEFAULT 0       COMMENT '当日粉丝数',
    `following_count`  BIGINT UNSIGNED  NOT NULL DEFAULT 0       COMMENT '当日关注数',
    `total_likes`      BIGINT UNSIGNED  NOT NULL DEFAULT 0       COMMENT '当日总获赞数',
    `total_plays`      BIGINT UNSIGNED  NOT NULL DEFAULT 0       COMMENT '当日总播放量',
    `video_count`      INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '当日总投稿视频数',
    -- 增量数据
    `follower_increment`  INT          DEFAULT NULL              COMMENT '粉丝增量',
    `total_likes_increment` BIGINT     DEFAULT NULL              COMMENT '获赞增量',
    `total_plays_increment` BIGINT     DEFAULT NULL              COMMENT '播放增量',
    -- 快照信息
    `snapshot_date`    DATE             NOT NULL                 COMMENT '快照日期 (YYYY-MM-DD)',
    `crawl_time`       DATETIME         NOT NULL                 COMMENT '精确采集时间',
    `created_at`       DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_up_uid_date` (`up_uid`, `snapshot_date`),
    KEY `idx_up_id` (`up_id`),
    KEY `idx_snapshot_date` (`snapshot_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='UP主每日数据快照表(历史趋势)';

-- ------------------------------------------------------------
-- 2.7 收藏夹表 (favorite_folders)
-- 描述: 用户创建的收藏夹分类
-- 来源: PRD 3.2.1 收藏管理 - "支持分类收藏夹"
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `favorite_folders`;
CREATE TABLE `favorite_folders` (
    `id`          BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT  COMMENT '收藏夹主键ID',
    `user_id`     BIGINT UNSIGNED  NOT NULL                 COMMENT '所属用户ID，外键关联users.id',
    `name`        VARCHAR(100)     NOT NULL                 COMMENT '收藏夹名称',
    `description` VARCHAR(500)     DEFAULT NULL             COMMENT '收藏夹描述',
    `is_public`   TINYINT(1)       NOT NULL DEFAULT 0       COMMENT '是否公开: 1-公开, 0-私有',
    `sort_order`  INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '排序序号，数字越小越靠前',
    `video_count` INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '收藏夹内视频数量(冗余计数)',
    `created_at`  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_user_sort` (`user_id`, `sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户收藏夹表';

-- ------------------------------------------------------------
-- 2.8 收藏记录表 (favorites)
-- 描述: 用户收藏的视频明细
-- 来源: PRD 3.2.1 收藏管理
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `favorites`;
CREATE TABLE `favorites` (
    `id`          BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT  COMMENT '收藏记录主键ID',
    `user_id`     BIGINT UNSIGNED  NOT NULL                 COMMENT '用户ID，外键关联users.id',
    `video_id`    BIGINT UNSIGNED  NOT NULL                 COMMENT '视频ID，外键关联videos.id',
    `folder_id`   BIGINT UNSIGNED  DEFAULT NULL             COMMENT '收藏夹ID，外键关联favorite_folders.id，NULL表示默认收藏',
    `note`        VARCHAR(500)     DEFAULT NULL             COMMENT '用户备注',
    `created_at`  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_video_folder` (`user_id`, `video_id`, `folder_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_video_id` (`video_id`),
    KEY `idx_folder_id` (`folder_id`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户收藏记录表';

-- ------------------------------------------------------------
-- 2.9 爬虫任务日志表 (crawl_logs)
-- 描述: 记录每次爬虫任务的执行情况
-- 来源: PRD 5.2 ER图 - crawl_logs
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `crawl_logs`;
CREATE TABLE `crawl_logs` (
    `id`             BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT  COMMENT '日志主键ID',
    `task_type`      VARCHAR(50)      NOT NULL                 COMMENT '任务类型: popular-热门榜, video_detail-视频详情, up_info-UP主信息, full_sync-全量同步',
    `status`         ENUM('pending','running','success','failed','partial') NOT NULL DEFAULT 'pending' COMMENT '任务状态: pending-等待, running-执行中, success-成功, failed-失败, partial-部分成功',
    `trigger_type`   ENUM('scheduled','manual') NOT NULL DEFAULT 'scheduled' COMMENT '触发方式: scheduled-定时触发, manual-手动触发',
    `total_videos`   INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '目标视频总数',
    `success_count`  INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '成功采集数',
    `failed_count`   INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '失败采集数',
    `skipped_count`  INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT '跳过数(已存在)',
    `error_msg`      TEXT             DEFAULT NULL             COMMENT '错误信息汇总',
    `started_at`     DATETIME         DEFAULT NULL             COMMENT '任务开始时间',
    `finished_at`    DATETIME         DEFAULT NULL             COMMENT '任务完成时间',
    `duration_ms`    INT UNSIGNED     DEFAULT NULL             COMMENT '任务耗时(毫秒)',
    `created_at`     DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_task_type` (`task_type`),
    KEY `idx_status` (`status`),
    KEY `idx_started_at` (`started_at`),
    KEY `idx_task_type_date` (`task_type`, `started_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='爬虫任务日志表';

-- ------------------------------------------------------------
-- 2.10 爬虫任务明细日志表 (crawl_log_details)
-- 描述: 记录每次爬虫任务中每个视频的采集详情，用于问题排查
-- 来源: PRD 9 风险应对 - 数据质量监控
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `crawl_log_details`;
CREATE TABLE `crawl_log_details` (
    `id`           BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT  COMMENT '明细日志主键ID',
    `log_id`       BIGINT UNSIGNED  NOT NULL                 COMMENT '关联crawl_logs.id',
    `bvid`         VARCHAR(20)      NOT NULL                 COMMENT '视频BV号',
    `api_step`     TINYINT UNSIGNED NOT NULL                 COMMENT 'API调用步骤: 1-热门列表, 2-视频详情, 3-UP主信息, 4-UP主统计, 5-UP主投稿, 6-UP主视频列表',
    `api_url`      VARCHAR(500)     DEFAULT NULL             COMMENT '请求的API地址',
    `status`       ENUM('success','failed','skipped') NOT NULL COMMENT '该步骤状态',
    `http_status`  SMALLINT         DEFAULT NULL             COMMENT 'HTTP响应状态码',
    `response_time_ms` INT UNSIGNED DEFAULT NULL             COMMENT '接口响应时间(毫秒)',
    `error_msg`    VARCHAR(1000)    DEFAULT NULL             COMMENT '错误信息',
    `retry_count`  TINYINT UNSIGNED NOT NULL DEFAULT 0       COMMENT '重试次数',
    `created_at`   DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_log_id` (`log_id`),
    KEY `idx_bvid` (`bvid`),
    KEY `idx_status` (`status`),
    KEY `idx_log_step` (`log_id`, `api_step`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='爬虫任务明细日志表';

-- ------------------------------------------------------------
-- 2.11 系统配置表 (system_configs)
-- 描述: 系统级配置项，如爬虫频率、数据保留策略等
-- 来源: PRD 3.2.2 爬虫调度配置 / 9 风险应对
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `system_configs`;
CREATE TABLE `system_configs` (
    `id`           BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT  COMMENT '配置主键ID',
    `config_key`   VARCHAR(100)     NOT NULL                 COMMENT '配置键名',
    `config_value` TEXT             NOT NULL                 COMMENT '配置值',
    `config_type`  VARCHAR(20)      NOT NULL DEFAULT 'string' COMMENT '配置值类型: string, int, float, bool, json',
    `description`  VARCHAR(500)     DEFAULT NULL             COMMENT '配置说明',
    `is_editable`  TINYINT(1)       NOT NULL DEFAULT 1       COMMENT '是否可通过管理界面修改: 1-可修改, 0-只读',
    `created_at`   DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`   DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_config_key` (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- ============================================================
-- 3. 初始化默认数据
-- ============================================================

-- 3.1 系统配置默认值
INSERT INTO `system_configs` (`config_key`, `config_value`, `config_type`, `description`, `is_editable`) VALUES
('crawl_interval_seconds', '7200', 'int', '爬虫执行间隔(秒)，默认2小时', 1),
('crawl_max_retry', '3', 'int', '单次API请求最大重试次数', 1),
('crawl_request_delay', '2', 'float', 'API请求间隔(秒)，反爬控制', 1),
('crawl_popular_pages', '2', 'int', '热门榜采集页数，每页50条', 1),
('data_retention_days', '90', 'int', '历史数据保留天数，超过自动归档', 1),
('data_anomaly_play_threshold', '0', 'int', '播放量异常阈值(负数标记异常)', 0),
('heat_formula_config', '{"play":0.3,"like":0.15,"comment":0.15,"danmaku":0.1,"coin":0.1,"favorite":0.1,"share":0.1}', 'json', '综合热度评分权重公式', 1),
('site_name', 'B站热门视频数据分析平台', 'string', '平台名称', 1),
('site_description', 'B站热门视频数据BI分析工具', 'string', '平台描述', 1);

-- 3.2 默认管理员账号 (密码: admin123, bcrypt加密)
-- 注意: 生产环境请立即修改密码
INSERT INTO `users` (`username`, `email`, `password_hash`, `nickname`, `role`, `email_verified`) VALUES
('admin', 'admin@bili-hot.com', '$2b$12$LJ3m4ys3GZfnYMz8kVsKaOTSxGHLfEhCgJwN5HGH3YR4RxGqHm5Oe', '系统管理员', 'admin', 1);

-- ============================================================
-- 4. 视图定义 (可选，方便常用查询)
-- ============================================================

-- 4.1 标签频次统计视图 (词云图数据源)
-- 用途: 按标签出现次数降序，直接用于词云图渲染
CREATE OR REPLACE VIEW v_tag_frequency AS
SELECT
    vt.tag_name,
    COUNT(DISTINCT vt.bvid) AS video_count,
    AVG(v.play_count)       AS avg_play_count,
    AVG(v.heat_score)       AS avg_heat_score,
    COUNT(DISTINCT v.partition_main) AS partition_count
FROM video_tags vt
LEFT JOIN videos v ON vt.bvid = v.bvid AND v.is_active = 1
GROUP BY vt.tag_name
ORDER BY video_count DESC;

-- 4.2 标签-分区交叉分析视图
-- 用途: 分析每个分区下最热门的标签，用于分区标签偏好分析
CREATE OR REPLACE VIEW v_tag_partition_stats AS
SELECT
    v.partition_main,
    vt.tag_name,
    COUNT(DISTINCT vt.bvid) AS video_count,
    AVG(v.play_count)       AS avg_play_count,
    AVG(v.heat_score)       AS avg_heat_score
FROM video_tags vt
INNER JOIN videos v ON vt.bvid = v.bvid AND v.is_active = 1
GROUP BY v.partition_main, vt.tag_name
ORDER BY v.partition_main, video_count DESC;

-- 4.3 今日热门视频TOP50视图 (含标签)
-- CREATE OR REPLACE VIEW v_today_hot_top50 AS
-- SELECT
--     v.bvid,
--     v.title,
--     v.play_count,
--     v.danmaku_count,
--     v.comment_count,
--     v.like_count,
--     v.coin_count,
--     v.favorite_count,
--     v.share_count,
--     v.interaction_rate,
--     v.heat_score,
--     v.partition_main,
--     v.duration,
--     v.pub_time,
--     u.nickname AS up_nickname,
--     u.level AS up_level,
--     u.follower_count AS up_follower_count,
--     GROUP_CONCAT(vt.tag_name SEPARATOR ',') AS tags
-- FROM videos v
-- LEFT JOIN up_users u ON v.up_id = u.id
-- LEFT JOIN video_tags vt ON v.bvid = vt.bvid
-- WHERE v.is_active = 1
--   AND DATE(v.crawl_time) = CURDATE()
-- GROUP BY v.id
-- ORDER BY v.heat_score DESC
-- LIMIT 50;

-- ============================================================
-- 5. 外键约束 (可选，根据项目需要启用)
-- ============================================================
-- 说明: 在高并发写入场景下，外键约束可能影响性能。
--       建议在应用层保证数据一致性，生产环境可按需启用。

-- ALTER TABLE `videos`
--     ADD CONSTRAINT `fk_videos_up_id` FOREIGN KEY (`up_id`) REFERENCES `up_users`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- ALTER TABLE `video_tags`
--     ADD CONSTRAINT `fk_video_tags_bvid` FOREIGN KEY (`bvid`) REFERENCES `videos`(`bvid`) ON DELETE CASCADE ON UPDATE CASCADE;

-- ALTER TABLE `video_snapshots`
--     ADD CONSTRAINT `fk_snapshots_video_id` FOREIGN KEY (`video_id`) REFERENCES `videos`(`id`) ON DELETE CASCADE ON UPDATE CASCADE,
--     ADD CONSTRAINT `fk_snapshots_up_id` FOREIGN KEY (`up_id`) REFERENCES `up_users`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- ALTER TABLE `up_user_snapshots`
--     ADD CONSTRAINT `fk_up_snapshots_up_id` FOREIGN KEY (`up_id`) REFERENCES `up_users`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- ALTER TABLE `favorite_folders`
--     ADD CONSTRAINT `fk_folders_user_id` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- ALTER TABLE `favorites`
--     ADD CONSTRAINT `fk_favorites_user_id` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE ON UPDATE CASCADE,
--     ADD CONSTRAINT `fk_favorites_video_id` FOREIGN KEY (`video_id`) REFERENCES `videos`(`id`) ON DELETE CASCADE ON UPDATE CASCADE,
--     ADD CONSTRAINT `fk_favorites_folder_id` FOREIGN KEY (`folder_id`) REFERENCES `favorite_folders`(`id`) ON DELETE SET NULL ON UPDATE CASCADE;

-- ALTER TABLE `crawl_log_details`
--     ADD CONSTRAINT `fk_crawl_details_log_id` FOREIGN KEY (`log_id`) REFERENCES `crawl_logs`(`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- ============================================================
-- 6. 数据归档存储过程 (可选)
-- ============================================================
-- 说明: 用于定期将超过保留天数的历史快照数据归档到归档表

-- DELIMITER //
-- CREATE PROCEDURE archive_old_snapshots(IN retention_days INT)
-- BEGIN
--     DECLARE archive_date DATE;
--     SET archive_date = DATE_SUB(CURDATE(), INTERVAL retention_days DAY);
--
--     -- 归档视频快照
--     INSERT INTO video_snapshots_archive
--     SELECT * FROM video_snapshots
--     WHERE snapshot_date < archive_date;
--
--     DELETE FROM video_snapshots
--     WHERE snapshot_date < archive_date;
--
--     -- 归档UP主快照
--     INSERT INTO up_user_snapshots_archive
--     SELECT * FROM up_user_snapshots
--     WHERE snapshot_date < archive_date;
--
--     DELETE FROM up_user_snapshots
--     WHERE snapshot_date < archive_date;
-- END //
-- DELIMITER ;

-- ============================================================
-- 文档结束
-- ============================================================