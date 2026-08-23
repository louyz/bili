import { useEffect, useState } from "react";
import { Row, Col, Card, Statistic, Spin } from "antd";
import { PlayCircleOutlined, VideoCameraOutlined, TeamOutlined, RiseOutlined } from "@ant-design/icons";
import * as echarts from "echarts";
import "echarts-wordcloud";
import ReactECharts from "echarts-for-react";
import { analysisApi, videoApi, type DashboardStats, type TrendPoint, type PartitionStat, type TagFrequency } from "../api";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [partitions, setPartitions] = useState<PartitionStat[]>([]);
  const [tags, setTags] = useState<TagFrequency[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      analysisApi.getDashboard(),
      analysisApi.getTrends(7),
      analysisApi.getPartitions(),
      analysisApi.getTags(30),
    ]).then(([s, t, p, tag]) => {
      setStats(s.data);
      setTrends(t.data);
      setPartitions(p.data);
      setTags(tag.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: "block", margin: "200px auto" }} />;

  const trendOption = {
    tooltip: { trigger: "axis" as const },
    xAxis: { type: "category" as const, data: trends.map((t) => t.date) },
    yAxis: { type: "value" as const, name: "平均播放量" },
    series: [
      {
        data: trends.map((t) => t.avg_play_count),
        type: "line",
        smooth: true,
        areaStyle: { color: "rgba(0,161,214,0.2)" },
        itemStyle: { color: "#00A1D6" },
      },
    ],
  };

  const partitionOption = {
    tooltip: { trigger: "item" as const },
    series: [
      {
        type: "pie",
        radius: ["40%", "70%"],
        data: partitions.map((p) => ({ name: p.partition, value: p.count })),
        label: { show: true, formatter: "{b}\n{d}%" },
      },
    ],
  };

  const tagWordCloud = {
    tooltip: {},
    series: [
      {
        type: "wordCloud",
        shape: "circle",
        sizeRange: [12, 40],
        rotationRange: [-45, 45],
        data: tags.map((t) => ({ name: t.tag_name, value: t.video_count })),
        emphasis: {
          focus: "self",
          textStyle: { color: "#00A1D6" },
        },
      },
    ],
  };

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>数据仪表盘</h2>
      <Row gutter={[16, 16]}>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title="总视频数" value={stats?.total_videos || 0} prefix={<VideoCameraOutlined />} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title="今日新增" value={stats?.today_new_videos || 0} prefix={<RiseOutlined />} valueStyle={{ color: "#3f8600" }} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title="平均播放量" value={stats?.avg_play_count || 0} prefix={<PlayCircleOutlined />} formatter={(v) => (Number(v) / 10000).toFixed(1) + "万"} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title="活跃UP主" value={stats?.active_up_count || 0} prefix={<TeamOutlined />} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card title="播放量趋势 (近7天)">
            <ReactECharts option={trendOption} style={{ height: 350 }} />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="分区分布">
            <ReactECharts option={partitionOption} style={{ height: 350 }} />
          </Card>
        </Col>
      </Row>

      <Row style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="热门标签词云">
            <ReactECharts option={tagWordCloud} style={{ height: 350 }} />
          </Card>
        </Col>
      </Row>
    </div>
  );
}