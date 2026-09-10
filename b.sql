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
CREATE DATABASE IF NOT EXISTS mydb
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE mydb;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for crawl_log_details
-- ----------------------------
DROP TABLE IF EXISTS `crawl_log_details`;
CREATE TABLE `crawl_log_details`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '明细日志主键ID',
  `log_id` bigint UNSIGNED NOT NULL COMMENT '关联crawl_logs.id',
  `bvid` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '视频BV号',
  `api_step` tinyint UNSIGNED NOT NULL COMMENT 'API调用步骤: 1-热门列表, 2-视频详情, 3-UP主信息, 4-UP主统计, 5-UP主投稿, 6-UP主视频列表',
  `api_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '请求的API地址',
  `status` enum('success','failed','skipped') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '该步骤状态',
  `http_status` smallint NULL DEFAULT NULL COMMENT 'HTTP响应状态码',
  `response_time_ms` int UNSIGNED NULL DEFAULT NULL COMMENT '接口响应时间(毫秒)',
  `error_msg` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '错误信息',
  `retry_count` tinyint UNSIGNED NOT NULL DEFAULT 0 COMMENT '重试次数',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_log_id`(`log_id` ASC) USING BTREE,
  INDEX `idx_bvid`(`bvid` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_log_step`(`log_id` ASC, `api_step` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '爬虫任务明细日志表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for crawl_logs
-- ----------------------------
DROP TABLE IF EXISTS `crawl_logs`;
CREATE TABLE `crawl_logs`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '日志主键ID',
  `task_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务类型: popular-热门榜, video_detail-视频详情, up_info-UP主信息, full_sync-全量同步',
  `status` enum('pending','running','success','failed','partial') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending' COMMENT '任务状态: pending-等待, running-执行中, success-成功, failed-失败, partial-部分成功',
  `trigger_type` enum('scheduled','manual') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'scheduled' COMMENT '触发方式: scheduled-定时触发, manual-手动触发',
  `total_videos` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '目标视频总数',
  `success_count` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '成功采集数',
  `failed_count` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '失败采集数',
  `skipped_count` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '跳过数(已存在)',
  `error_msg` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '错误信息汇总',
  `started_at` datetime NULL DEFAULT NULL COMMENT '任务开始时间',
  `finished_at` datetime NULL DEFAULT NULL COMMENT '任务完成时间',
  `duration_ms` int UNSIGNED NULL DEFAULT NULL COMMENT '任务耗时(毫秒)',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_task_type`(`task_type` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_started_at`(`started_at` ASC) USING BTREE,
  INDEX `idx_task_type_date`(`task_type` ASC, `started_at` ASC) USING BTREE
) ENGINE = InnoDB  CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '爬虫任务日志表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for favorite_folders
-- ----------------------------
DROP TABLE IF EXISTS `favorite_folders`;
CREATE TABLE `favorite_folders`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '收藏夹主键ID',
  `user_id` bigint UNSIGNED NOT NULL COMMENT '所属用户ID，外键关联users.id',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '收藏夹名称',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '收藏夹描述',
  `is_public` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否公开: 1-公开, 0-私有',
  `sort_order` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '排序序号，数字越小越靠前',
  `video_count` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '收藏夹内视频数量(冗余计数)',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_user_sort`(`user_id` ASC, `sort_order` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户收藏夹表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for favorites
-- ----------------------------
DROP TABLE IF EXISTS `favorites`;
CREATE TABLE `favorites`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '收藏记录主键ID',
  `user_id` bigint UNSIGNED NOT NULL COMMENT '用户ID，外键关联users.id',
  `video_id` bigint UNSIGNED NOT NULL COMMENT '视频ID，外键关联videos.id',
  `folder_id` bigint UNSIGNED NULL DEFAULT NULL COMMENT '收藏夹ID，外键关联favorite_folders.id，NULL表示默认收藏',
  `note` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '用户备注',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_user_video_folder`(`user_id` ASC, `video_id` ASC, `folder_id` ASC) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_video_id`(`video_id` ASC) USING BTREE,
  INDEX `idx_folder_id`(`folder_id` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户收藏记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for system_configs
-- ----------------------------
DROP TABLE IF EXISTS `system_configs`;
CREATE TABLE `system_configs`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '配置主键ID',
  `config_key` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '配置键名',
  `config_value` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '配置值',
  `config_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'string' COMMENT '配置值类型: string, int, float, bool, json',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '配置说明',
  `is_editable` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否可通过管理界面修改: 1-可修改, 0-只读',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_config_key`(`config_key` ASC) USING BTREE
) ENGINE = InnoDB  CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '系统配置表' ROW_FORMAT = Dynamic;


INSERT INTO `system_configs` VALUES (1, 'crawl_interval_seconds', '7200', 'int', '爬虫执行间隔(秒)，默认2小时', 1, '2026-09-09 15:43:43', '2026-09-09 15:43:43');
INSERT INTO `system_configs` VALUES (2, 'crawl_max_retry', '3', 'int', '单次API请求最大重试次数', 1, '2026-09-09 15:43:43', '2026-09-09 15:43:43');
INSERT INTO `system_configs` VALUES (3, 'crawl_request_delay', '2', 'float', 'API请求间隔(秒)，反爬控制', 1, '2026-09-09 15:43:43', '2026-09-09 15:43:43');
INSERT INTO `system_configs` VALUES (4, 'crawl_popular_pages', '2', 'int', '热门榜采集页数，每页50条', 1, '2026-09-09 15:43:43', '2026-09-09 15:43:43');
INSERT INTO `system_configs` VALUES (5, 'data_retention_days', '90', 'int', '历史数据保留天数，超过自动归档', 1, '2026-09-09 15:43:43', '2026-09-09 15:43:43');
INSERT INTO `system_configs` VALUES (6, 'data_anomaly_play_threshold', '0', 'int', '播放量异常阈值(负数标记异常)', 0, '2026-09-09 15:43:43', '2026-09-09 15:43:43');
INSERT INTO `system_configs` VALUES (7, 'heat_formula_config', '{\"play\":0.3,\"like\":0.15,\"comment\":0.15,\"danmaku\":0.1,\"coin\":0.1,\"favorite\":0.1,\"share\":0.1}', 'json', '综合热度评分权重公式', 1, '2026-09-09 15:43:43', '2026-09-09 15:43:43');
INSERT INTO `system_configs` VALUES (8, 'site_name', 'B站热门视频数据分析平台', 'string', '平台名称', 1, '2026-09-09 15:43:43', '2026-09-09 15:43:43');
INSERT INTO `system_configs` VALUES (9, 'site_description', 'B站热门视频数据BI分析工具', 'string', '平台描述', 1, '2026-09-09 15:43:43', '2026-09-09 15:43:43');



-- ----------------------------
-- Table structure for up_users
-- ----------------------------
DROP TABLE IF EXISTS `up_users`;
CREATE TABLE `up_users`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'UP主记录主键ID',
  `up_uid` bigint UNSIGNED NOT NULL COMMENT 'B站UP主UID (mid)，B站唯一标识',
  `nickname` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'UP主昵称',
  `sex` enum('男','女','保密') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '保密' COMMENT 'UP主性别',
  `level` tinyint UNSIGNED NULL DEFAULT 0 COMMENT 'UP主等级，范围 Lv0-Lv6',
  `sign` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'UP主个人签名/简介',
  `avatar_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'UP主头像URL',
  `official_role` tinyint UNSIGNED NOT NULL DEFAULT 0 COMMENT '认证类型: 0=无,1=个人,2=机构,3=媒体,4=政府,5=电视,6=明星,7=虚拟主播',
  `official_title` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '认证称号',
  `follower_count` bigint UNSIGNED NULL DEFAULT 0 COMMENT '粉丝数',
  `following_count` bigint UNSIGNED NULL DEFAULT 0 COMMENT '关注数',
  `total_likes` bigint UNSIGNED NULL DEFAULT 0 COMMENT '总获赞数',
  `total_plays` bigint UNSIGNED NULL DEFAULT 0 COMMENT '总播放量',
  `video_count` bigint UNSIGNED NULL DEFAULT 0 COMMENT '视频数',
  `elec` bigint NULL DEFAULT NULL COMMENT '充电总数',
  `total` bigint NULL DEFAULT NULL COMMENT '总作品数',
  `audio_count` bigint NULL DEFAULT NULL COMMENT '音频数',
  `image_text_count` bigint NULL DEFAULT NULL COMMENT '图文数',
  `crawl_time` datetime NOT NULL COMMENT '本次数据采集时间',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次录入时间',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最近更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_up_uid`(`up_uid` ASC) USING BTREE,
  INDEX `idx_nickname`(`nickname` ASC) USING BTREE,
  INDEX `idx_follower_count`(`follower_count` ASC) USING BTREE,
  INDEX `idx_level`(`level` ASC) USING BTREE,
  INDEX `idx_crawl_time`(`crawl_time` ASC) USING BTREE
) ENGINE = InnoDB  CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'UP主信息表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户主键ID',
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户名，用于登录',
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '邮箱，用于注册验证和找回密码',
  `password_hash` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码哈希值，bcrypt加密',
  `avatar_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '用户头像URL',
  `nickname` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '用户昵称，展示用',
  `role` enum('user','admin') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'user' COMMENT '用户角色: user-普通用户, admin-管理员',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '账号状态: 1-启用, 0-禁用',
  `email_verified` tinyint(1) NOT NULL DEFAULT 0 COMMENT '邮箱是否已验证: 1-已验证, 0-未验证',
  `last_login_at` datetime NULL DEFAULT NULL COMMENT '最后登录时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_username`(`username` ASC) USING BTREE,
  UNIQUE INDEX `uk_email`(`email` ASC) USING BTREE,
  INDEX `idx_role`(`role` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE
) ENGINE = InnoDB  CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户表' ROW_FORMAT = Dynamic;


INSERT INTO `users` VALUES (1, 'admin', 'admin@bili-hot.com', '0192023a7bbd73250516f069df18b500', NULL, '系统管理员', 'admin', 1, 1, NULL, '2026-09-09 15:43:43', '2026-09-09 17:10:40');

-- ----------------------------
-- Table structure for video_tags
-- ----------------------------
DROP TABLE IF EXISTS `video_tags`;
CREATE TABLE `video_tags`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '标签记录主键ID',
  `bvid` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'B站视频BV号，关联videos.bvid',
  `tag_id` int NULL DEFAULT NULL COMMENT '标签id',
  `tag_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '标签名称',
  `crawl_time` datetime NOT NULL COMMENT '本次标签采集时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_bvid_tag`(`bvid` ASC, `tag_name` ASC) USING BTREE,
  INDEX `idx_bvid`(`bvid` ASC) USING BTREE,
  INDEX `idx_tag_name`(`tag_name` ASC) USING BTREE,
  INDEX `idx_crawl_time`(`crawl_time` ASC) USING BTREE,
  INDEX `idx_tag_crawl`(`tag_name` ASC, `crawl_time` ASC) USING BTREE
) ENGINE = InnoDB  CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '视频标签关联表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for videos
-- ----------------------------
DROP TABLE IF EXISTS `videos`;
CREATE TABLE `videos`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '视频记录主键ID',
  `bvid` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'B站视频BV号，唯一标识一个视频',
  `title` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '视频标题',
  `cover_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '视频封面图URL',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '视频简介/描述',
  `play_count` bigint UNSIGNED NOT NULL DEFAULT 0 COMMENT '播放量',
  `danmaku_count` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '弹幕数',
  `comment_count` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '评论数',
  `like_count` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '点赞数',
  `coin_count` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '投币数',
  `favorite_count` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '收藏数',
  `share_count` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '转发数',
  `duration` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '视频时长(秒)',
  `pub_time` datetime NOT NULL COMMENT '视频发布时间',
  `pub_location` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '发布地点',
  `partition_main` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '未知' COMMENT '一级分区名称，如\"动画\"、\"游戏\"',
  `partition_sub` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '二级分区名称',
  `up_id` bigint UNSIGNED NOT NULL COMMENT '关联UP主记录ID，外键关联up_users.id',
  `up_uid` bigint UNSIGNED NOT NULL COMMENT 'B站UP主UID (冗余字段，方便查询)',
  `interaction_rate` decimal(8, 6) NULL DEFAULT NULL COMMENT '互动率 = (点赞+评论+弹幕+投币+收藏+转发)/播放量',
  `heat_score` decimal(12, 2) NULL DEFAULT NULL COMMENT '综合热度评分 = 播放量×0.3 + 点赞×0.15 + 评论×0.15 + 弹幕×0.1 + 投币×0.1 + 收藏×0.1 + 转发×0.1',
  `crawl_time` datetime NOT NULL COMMENT '本次数据采集时间',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '数据状态: 1-正常, 0-异常/已排除',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次录入时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最近更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_bvid`(`bvid` ASC) USING BTREE,
  INDEX `idx_up_id`(`up_id` ASC) USING BTREE,
  INDEX `idx_up_uid`(`up_uid` ASC) USING BTREE,
  INDEX `idx_play_count`(`play_count` ASC) USING BTREE,
  INDEX `idx_pub_time`(`pub_time` ASC) USING BTREE,
  INDEX `idx_partition_main`(`partition_main` ASC) USING BTREE,
  INDEX `idx_crawl_time`(`crawl_time` ASC) USING BTREE,
  INDEX `idx_interaction_rate`(`interaction_rate` ASC) USING BTREE,
  INDEX `idx_heat_score`(`heat_score` ASC) USING BTREE,
  INDEX `idx_is_active`(`is_active` ASC) USING BTREE,
  INDEX `idx_partition_pub`(`partition_main` ASC, `pub_time` ASC) USING BTREE
) ENGINE = InnoDB  CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '热门视频表(最新快照)' ROW_FORMAT = Dynamic;

-- ----------------------------
-- View structure for v_tag_frequency
-- ----------------------------
DROP VIEW IF EXISTS `v_tag_frequency`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `v_tag_frequency` AS select `vt`.`tag_name` AS `tag_name`,count(distinct `vt`.`bvid`) AS `video_count`,avg(`v`.`play_count`) AS `avg_play_count`,avg(`v`.`heat_score`) AS `avg_heat_score`,count(distinct `v`.`partition_main`) AS `partition_count` from (`video_tags` `vt` left join `videos` `v` on(((`vt`.`bvid` = `v`.`bvid`) and (`v`.`is_active` = 1)))) group by `vt`.`tag_name` order by `video_count` desc;

-- ----------------------------
-- View structure for v_tag_partition_stats
-- ----------------------------
DROP VIEW IF EXISTS `v_tag_partition_stats`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `v_tag_partition_stats` AS select `v`.`partition_main` AS `partition_main`,`vt`.`tag_name` AS `tag_name`,count(distinct `vt`.`bvid`) AS `video_count`,avg(`v`.`play_count`) AS `avg_play_count`,avg(`v`.`heat_score`) AS `avg_heat_score` from (`video_tags` `vt` join `videos` `v` on(((`vt`.`bvid` = `v`.`bvid`) and (`v`.`is_active` = 1)))) group by `v`.`partition_main`,`vt`.`tag_name` order by `v`.`partition_main`,`video_count` desc;

SET FOREIGN_KEY_CHECKS = 1;