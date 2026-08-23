import { useEffect, useState } from "react";
import { Card, Row, Col, Select, Spin, Table } from "antd";
import ReactECharts from "echarts-for-react";
import { analysisApi, type TrendPoint, type PartitionStat, type TagFrequency } from "../api";

export default function AnalysisPage() {
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [partitions, setPartitions] = useState<PartitionStat[]>([]);
  const [tags, setTags] = useState<TagFrequency[]>([]);
  const [upRank, setUpRank] = useState<any[]>([]);
  const [trendDays, setTrendDays] = useState(7);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      analysisApi.getTrends(trendDays),
      analysisApi.getPartitions(),
      analysisApi.getTags(50),
      analysisApi.getUpRank(20),
    ]).then(([t, p, tag, up]) => {
      setTrends(t.data);
      setPartitions(p.data);
      setTags(tag.data);
      setUpRank(up.data);
    }).finally(() => setLoading(false));
  }, [trendDays]);

  if (loading) return <Spin size="large" style={{ display: "block", margin: "200px auto" }} />;

  const trendOption = {
    tooltip: { trigger: "axis" as const },
    legend: { data: ["平均播放量", "视频数量"] },
    xAxis: { type: "category" as const, data: trends.map((t) => t.date) },
    yAxis: [
      { type: "value" as const, name: "播放量" },
      { type: "value" as const, name: "数量" },
    ],
    series: [
      {
        name: "平均播放量",
        data: trends.map((t) => t.avg_play_count),
        type: "line",
        smooth: true,
        areaStyle: { color: "rgba(0,161,214,0.2)" },
        itemStyle: { color: "#00A1D6" },
      },
      {
        name: "视频数量",
        data: trends.map((t) => t.video_count),
        type: "bar",
        yAxisIndex: 1,
        itemStyle: { color: "#ff7875" },
      },
    ],
  };

  const partitionOption = {
    tooltip: { trigger: "item" as const },
    series: [
      {
        type: "pie",
        radius: "65%",
        data: partitions.map((p) => ({ name: p.partition, value: p.count })),
        emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: "rgba(0,0,0,0.5)" } },
      },
    ],
  };

  const tagOption = {
    tooltip: { trigger: "item" as const },
    xAxis: { type: "category" as const, data: tags.slice(0, 20).map((t) => t.tag_name), axisLabel: { rotate: 45 } },
    yAxis: { type: "value" as const },
    series: [
      {
        type: "bar",
        data: tags.slice(0, 20).map((t) => ({ value: t.video_count, name: t.tag_name })),
        itemStyle: {
          color: {
            type: "linear",
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: "#00A1D6" },
              { offset: 1, color: "#87e8de" },
            ],
          },
        },
      },
    ],
  };

  const upColumns = [
    { title: "排名", render: (_: any, __: any, i: number) => i + 1, width: 60 },
    { title: "UP主UID", dataIndex: "up_uid", width: 120 },
    { title: "视频数", dataIndex: "video_count", width: 80 },
    {
      title: "平均播放量",
      dataIndex: "avg_play_count",
      render: (v: number) => (v / 10000).toFixed(1) + "万",
    },
    {
      title: "平均热度",
      dataIndex: "avg_heat_score",
      render: (v: number) => (v / 10000).toFixed(1) + "万",
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>数据分析</h2>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={24}>
          <Card
            title="播放量趋势"
            extra={
              <Select
                value={trendDays}
                onChange={setTrendDays}
                options={[
                  { value: 7, label: "近7天" },
                  { value: 30, label: "近30天" },
                  { value: 90, label: "近90天" },
                ]}
                size="small"
              />
            }
          >
            <ReactECharts option={trendOption} style={{ height: 350 }} />
          </Card>
        </Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="分区分布">
            <ReactECharts option={partitionOption} style={{ height: 350 }} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="热门标签 TOP20">
            <ReactECharts option={tagOption} style={{ height: 350 }} />
          </Card>
        </Col>
      </Row>
      <Row style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="UP主影响力排名 TOP20">
            <Table columns={upColumns} dataSource={upRank} rowKey="up_uid" pagination={false} size="small" />
          </Card>
        </Col>
      </Row>
    </div>
  );
}