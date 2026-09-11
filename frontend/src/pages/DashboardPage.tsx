import { useEffect, useState } from "react";
import { Row, Col, Card, Statistic, Spin } from "antd";
import { PlayCircleOutlined, VideoCameraOutlined, TeamOutlined, RiseOutlined } from "@ant-design/icons";
import "echarts-wordcloud";
import ReactECharts from "echarts-for-react";
import { analysisApi, type DashboardStats, type TrendPoint, type PartitionHierarchyNode, type TagFrequency } from "../api";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [partitions, setPartitions] = useState<PartitionHierarchyNode[]>([]);
  const [tags, setTags] = useState<TagFrequency[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      analysisApi.getDashboard(),
      analysisApi.getTrends(7),
      analysisApi.getPartitionsHierarchy(),
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

  const partitionOption = (() => {
    const subWithParent = partitions.flatMap((p) =>
      (p.children || []).map((c) => ({ parent: p, child: c }))
    );
    const topSubs = subWithParent
      .sort((a, b) => b.child.value - a.child.value)
      .slice(0, 30);

    const grouped = new Map<string, PartitionHierarchyNode>();
    topSubs.forEach(({ parent, child }) => {
      let entry = grouped.get(parent.name);
      if (!entry) {
        entry = { ...parent, value: 0, children: [] };
        grouped.set(parent.name, entry);
      }
      entry.children!.push(child);
      entry.value += child.value;
    });
    const topPartitions = Array.from(grouped.values());

    const allNodes: PartitionHierarchyNode[] = [];
    topPartitions.forEach((p) => {
      allNodes.push(p);
      if (p.children) allNodes.push(...p.children);
    });
    const rates = allNodes.map((n) => n.avg_interaction_rate || 0);
    const minR = rates.length ? Math.min(...rates) : 0;
    const maxR = rates.length ? Math.max(...rates) : 1;

    const colorStops = [
      { t: 0, c: [105, 192, 255] },
      { t: 0.5, c: [0, 161, 214] },
      { t: 1, c: [250, 84, 28] },
    ];
    const colorFor = (rate: number) => {
      if (maxR === minR) return "rgb(0,161,214)";
      const t = Math.min(1, Math.max(0, (rate - minR) / (maxR - minR)));
      let lo = colorStops[0], hi = colorStops[colorStops.length - 1];
      for (let i = 0; i < colorStops.length - 1; i++) {
        if (t >= colorStops[i].t && t <= colorStops[i + 1].t) {
          lo = colorStops[i];
          hi = colorStops[i + 1];
          break;
        }
      }
      const span = hi.t - lo.t || 1;
      const k = (t - lo.t) / span;
      const r = Math.round(lo.c[0] + (hi.c[0] - lo.c[0]) * k);
      const g = Math.round(lo.c[1] + (hi.c[1] - lo.c[1]) * k);
      const b = Math.round(lo.c[2] + (hi.c[2] - lo.c[2]) * k);
      return `rgb(${r},${g},${b})`;
    };

    type SunburstNode = {
      name: string;
      value: number;
      avg_heat_score: number;
      avg_interaction_rate: number;
      itemStyle: { color: string };
      children?: SunburstNode[];
    };
    const buildNode = (n: PartitionHierarchyNode): SunburstNode => ({
      name: n.name,
      value: n.value,
      avg_heat_score: n.avg_heat_score,
      avg_interaction_rate: n.avg_interaction_rate,
      itemStyle: { color: colorFor(n.avg_interaction_rate || 0) },
      children: (n.children || []).map(buildNode),
    });
    const data = topPartitions.map(buildNode);

    const legendGraphics = [
      { left: "18%", color: "rgb(105,192,255)", label: "低" },
      { left: "38%", color: "rgb(0,161,214)", label: "中" },
      { left: "58%", color: "rgb(250,140,80)", label: "高" },
      { left: "78%", color: "rgb(250,84,28)", label: "极高" },
    ].map((g) => ({
      type: "group" as const,
      left: g.left,
      bottom: 2,
      children: [
        {
          type: "rect" as const,
          shape: { x: 0, y: 0, width: 14, height: 10 },
          style: { fill: g.color, stroke: "#fff", lineWidth: 1 },
        },
        {
          type: "text" as const,
          style: { text: g.label, x: 18, y: 1, fontSize: 10, fill: "#666" },
          z: 100,
        },
      ],
    }));

    return {
      tooltip: {
        formatter: (p: any) => {
          const d = p.data;
          return `${p.name}<br/>视频数: ${d.value}<br/>平均热度: ${(d.avg_heat_score || 0).toLocaleString()}<br/>平均互动率: ${((d.avg_interaction_rate || 0) * 100).toFixed(2)}%`;
        },
      },
      graphic: [
        ...legendGraphics,
        {
          type: "text" as const,
          top: 2,
          left: "center",
          style: { text: "颜色 = 平均互动率", fontSize: 10, fill: "#999" },
        },
      ],
      series: [
        {
          type: "sunburst",
          radius: ["18%", "85%"],
          center: ["50%", "52%"],
          data,
          nodeClick: false,
          label: {
            rotate: "radial" as const,
            fontSize: 10,
            formatter: (p: any) => (p.data.value > 0 ? p.name : ""),
          },
          itemStyle: { borderColor: "#fff", borderWidth: 1 },
        },
      ],
    };
  })();

  const tagWordCloud = (() => {
    const counts = tags.map((t) => t.video_count);
    const minC = counts.length ? Math.min(...counts) : 0;
    const maxC = counts.length ? Math.max(...counts) : 1;
    const stops = [
      { t: 0, c: [105, 192, 255] },
      { t: 0.5, c: [0, 161, 214] },
      { t: 1, c: [250, 84, 28] },
    ];
    const colorFor = (count: number) => {
      if (maxC === minC) return "rgb(0,161,214)";
      const t = Math.min(1, Math.max(0, (count - minC) / (maxC - minC)));
      let lo = stops[0], hi = stops[stops.length - 1];
      for (let i = 0; i < stops.length - 1; i++) {
        if (t >= stops[i].t && t <= stops[i + 1].t) {
          lo = stops[i];
          hi = stops[i + 1];
          break;
        }
      }
      const span = hi.t - lo.t || 1;
      const k = (t - lo.t) / span;
      const r = Math.round(lo.c[0] + (hi.c[0] - lo.c[0]) * k);
      const g = Math.round(lo.c[1] + (hi.c[1] - lo.c[1]) * k);
      const b = Math.round(lo.c[2] + (hi.c[2] - lo.c[2]) * k);
      return `rgb(${r},${g},${b})`;
    };

    return {
      tooltip: {
        formatter: (p: any) => `${p.name}<br/>视频数: ${p.value}`,
      },
      series: [
        {
          type: "wordCloud",
          shape: "circle",
          sizeRange: [12, 40],
          rotationRange: [-45, 45],
          data: tags.map((t) => ({
            name: t.tag_name,
            value: t.video_count,
            textStyle: { color: colorFor(t.video_count) },
          })),
          emphasis: {
            focus: "self",
            textStyle: { textShadowBlur: 6, textShadowColor: "rgba(0,0,0,0.3)" },
          },
        },
      ],
    };
  })();

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
          <Card title="分区分布（内环=一级 / 外环=二级，颜色=互动率）">
            <ReactECharts option={partitionOption} style={{ height: 380 }} />
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