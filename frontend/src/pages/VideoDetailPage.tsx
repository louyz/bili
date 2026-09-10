import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Descriptions, Tag, Button, Spin, Avatar, Row, Col, Statistic, message } from "antd";
import { ArrowLeftOutlined, PlayCircleOutlined, LikeOutlined, CommentOutlined, StarOutlined } from "@ant-design/icons";
import ReactECharts from "echarts-for-react";
import { videoApi, favApi, type VideoDetail } from "../api";
import { proxyImage } from "../utils/proxy";

export default function VideoDetailPage() {
  const { bvid } = useParams<{ bvid: string }>();
  const [video, setVideo] = useState<VideoDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (!bvid) return;
    const controller = new AbortController();
    setLoading(true);
    videoApi.getDetail(bvid, { signal: controller.signal })
      .then((res) => setVideo(res.data))
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [bvid]);

  const handleFavorite = async () => {
    if (!bvid) return;
    try {
      await favApi.addVideo(bvid);
      message.success("收藏成功");
    } catch (err: any) {
      message.error(err.response?.data?.detail || "收藏失败");
    }
  };

  if (loading) return <Spin size="large" style={{ display: "block", margin: "200px auto" }} />;
  if (!video) return <div>视频不存在</div>;

  const formatNum = (n: number) => (n >= 10000 ? (n / 10000).toFixed(1) + "万" : String(n));

  const radarValues = [
    video.play_count,
    video.like_count,
    video.comment_count,
    video.danmaku_count,
    video.coin_count,
    video.favorite_count,
  ];
  const radarMax = Math.max(...radarValues, 1) * 1.2;

  const radarLabels = ["播放", "点赞", "评论", "弹幕", "投币", "收藏"];

  const radarOption = {
    tooltip: {
      trigger: "item",
      formatter: (params: any) => {
        const values = params.value as number[];
        const lines = radarLabels.map((label, i) => {
          return `${label}: ${formatNum(values[i])}`;
        });
        return `${params.name}<br/>${lines.join("<br/>")}`;
      },
    },
    radar: {
      shape: "polygon",
      radius: "65%",
      indicator: [
        { name: "播放", max: radarMax },
        { name: "点赞", max: radarMax },
        { name: "评论", max: radarMax },
        { name: "弹幕", max: radarMax },
        { name: "投币", max: radarMax },
        { name: "收藏", max: radarMax },
      ],
    },
    series: [
      {
        type: "radar",
        data: [
          {
            value: radarValues,
            name: video.title,
            areaStyle: { color: "rgba(0,161,214,0.3)" },
            lineStyle: { color: "#00a1d6", width: 2 },
            itemStyle: { color: "#00a1d6" },
            label: {
              show: true,
              formatter: (params: any) => {
                const idx = params.dimensionIndex;
                return formatNum(radarValues[idx]);
              },
            },
          },
        ],
      },
    ],
  };

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)} style={{ marginBottom: 16 }}>
        返回
      </Button>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card>
            <h2>{video.title}</h2>
            <div style={{ marginTop: 16 }}>
              <Button
                type="primary"
                icon={<StarOutlined />}
                onClick={handleFavorite}
              >
                收藏视频
              </Button>
              <Button
                style={{ marginLeft: 8 }}
                onClick={() => window.open(`https://www.bilibili.com/video/${video.bvid}`, "_blank")}
              >
                在B站观看
              </Button>
            </div>
            <Row gutter={16} style={{ marginTop: 24 }}>
              <Col span={8}>
                <Statistic title="播放量" value={video.play_count} prefix={<PlayCircleOutlined />} formatter={(v) => formatNum(Number(v))} />
              </Col>
              <Col span={8}>
                <Statistic title="点赞数" value={video.like_count} prefix={<LikeOutlined />} />
              </Col>
              <Col span={8}>
                <Statistic title="评论数" value={video.comment_count} prefix={<CommentOutlined />} />
              </Col>
            </Row>
            <Row gutter={16} style={{ marginTop: 16 }}>
              <Col span={8}>
                <Statistic title="弹幕数" value={video.danmaku_count} />
              </Col>
              <Col span={8}>
                <Statistic title="投币数" value={video.coin_count} />
              </Col>
              <Col span={8}>
                <Statistic title="分享数" value={video.share_count} />
              </Col>
            </Row>
            <Descriptions style={{ marginTop: 24 }} column={2} size="small" bordered>
              <Descriptions.Item label="BV号">{video.bvid}</Descriptions.Item>
              <Descriptions.Item label="分区">
                <Tag color="blue">{video.partition_main}</Tag>
                {video.partition_sub && <Tag>{video.partition_sub}</Tag>}
              </Descriptions.Item>
              <Descriptions.Item label="发布时间">{new Date(video.pub_time).toLocaleString()}</Descriptions.Item>
              <Descriptions.Item label="互动率">{(video.interaction_rate * 100).toFixed(2)}%</Descriptions.Item>
              <Descriptions.Item label="热度评分">{formatNum(video.heat_score)}</Descriptions.Item>
              <Descriptions.Item label="视频简介" span={2}>
                {video.description || "暂无简介"}
              </Descriptions.Item>
              <Descriptions.Item label="标签" span={2}>
                {video.tags?.map((t) => <Tag key={t}>{t}</Tag>) || "无标签"}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          {video.up_user && (
            <Card title="UP主信息">
              <div style={{ textAlign: "center", marginBottom: 16 }}>
                <Avatar size={80} src={proxyImage(video.up_user.avatar_url)} />
                <h3 style={{ marginTop: 8 }}>{video.up_user.nickname}</h3>
                <Tag color="pink">Lv{video.up_user.level}</Tag>
              </div>
              <p style={{ color: "#666" }}>{video.up_user.sign || "暂无签名"}</p>
              <Row gutter={8} style={{ marginTop: 16 }}>
                <Col span={12}>
                  <Statistic title="粉丝" value={video.up_user.follower_count} formatter={(v) => formatNum(Number(v))} />
                </Col>
                <Col span={12}>
                  <Statistic title="总播放" value={video.up_user.total_plays} formatter={(v) => formatNum(Number(v))} />
                </Col>
              </Row>
              <Row gutter={8} style={{ marginTop: 8 }}>
                <Col span={12}>
                  <Statistic title="视频数" value={video.up_user.video_count} />
                </Col>
                <Col span={12}>
                  <Statistic title="总获赞" value={video.up_user.total_likes} formatter={(v) => formatNum(Number(v))} />
                </Col>
              </Row>
            </Card>
          )}
          <Card title="数据雷达图" style={{ marginTop: 16 }}>
            <ReactECharts option={radarOption} notMerge style={{ height: 300 }} />
          </Card>
        </Col>
      </Row>
    </div>
  );
}