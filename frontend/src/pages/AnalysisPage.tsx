import { useEffect, useState } from "react";
import { Card, Row, Col, Select, Spin, Table } from "antd";
import ReactECharts from "echarts-for-react";
import { analysisApi, type TrendPoint, type TagFrequency, type UpContribution, type InteractionItem, type PartitionImpactItem, type DurationImpactItem, type PubTimeHeatItem } from "../api";

export default function AnalysisPage() {
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [tags, setTags] = useState<TagFrequency[]>([]);
  const [upRank, setUpRank] = useState<any[]>([]);
  const [upContributions, setUpContributions] = useState<UpContribution[]>([]);
  const [interaction, setInteraction] = useState<InteractionItem[]>([]);
  const [partitionImpact, setPartitionImpact] = useState<PartitionImpactItem[]>([]);
  const [durationImpact, setDurationImpact] = useState<DurationImpactItem[]>([]);
  const [pubTimeHeat, setPubTimeHeat] = useState<PubTimeHeatItem[]>([]);
  const [trendDays, setTrendDays] = useState(7);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      analysisApi.getTrends(trendDays),
      analysisApi.getTags(50),
      analysisApi.getUpRank(20),
      analysisApi.getUpContribution(40),
      analysisApi.getInteractionStructure(),
      analysisApi.getPartitionImpact(15),
      analysisApi.getDurationImpact(),
      analysisApi.getPubTimeHeatmap(),
    ]).then(([t, tag, up, contrib, inter, pImpact, dImpact, heat]) => {
      setTrends(t.data);
      setTags(tag.data);
      setUpRank(up.data);
      setUpContributions(contrib.data);
      setInteraction(inter.data);
      setPartitionImpact(pImpact.data);
      setDurationImpact(dImpact.data);
      setPubTimeHeat(heat.data);
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

  const tagDistData = (() => {
    const top = tags.slice(0, 20);
    const rest = tags.slice(20);
    const restTotal = rest.reduce((sum, t) => sum + t.video_count, 0);
    const data = top.map((t) => ({ name: t.tag_name, value: t.video_count }));
    if (restTotal > 0) data.push({ name: "其余标签", value: restTotal });
    return data;
  })();

  const tagDistOption = {
    tooltip: {
      trigger: "item" as const,
      formatter: "{b}: {c} ({d}%)",
    },
    legend: {
      type: "scroll" as const,
      orient: "vertical" as const,
      right: 10,
      top: 20,
      bottom: 20,
      data: tagDistData.map((d) => d.name),
    },
    series: [
      {
        type: "pie",
        radius: ["35%", "65%"],
        center: ["40%", "50%"],
        data: tagDistData,
        emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: "rgba(0,0,0,0.5)" } },
        label: { formatter: "{b}: {d}%" },
      },
    ],
  };

  const tagPlaySorted = [...tags].sort((a, b) => b.avg_play_count - a.avg_play_count).slice(0, 20);

  const tagPlayOption = {
    tooltip: {
      trigger: "axis" as const,
      axisPointer: { type: "cross" as const },
      formatter: (params: any) => {
        const idx = params[0].dataIndex;
        const item = tagPlaySorted[idx];
        return `${item.tag_name}<br/>视频数: ${item.video_count}<br/>平均播放: ${item.avg_play_count.toLocaleString()}<br/>热度: ${item.avg_heat_score.toLocaleString()}`;
      },
    },
    legend: { data: ["视频数", "平均播放量"] },
    grid: { left: "3%", right: "4%", bottom: "10%", containLabel: true },
    xAxis: {
      type: "category" as const,
      data: tagPlaySorted.map((t) => t.tag_name),
      axisLabel: { rotate: 45, interval: 0 },
    },
    yAxis: [
      { type: "value" as const, name: "视频数", position: "left" },
      { type: "value" as const, name: "平均播放量", position: "right", axisLabel: { formatter: (v: number) => (v >= 10000 ? v / 10000 + "万" : String(v)) } },
    ],
    series: [
      {
        name: "视频数",
        type: "bar",
        yAxisIndex: 0,
        data: tagPlaySorted.map((t) => t.video_count),
        itemStyle: { color: "#00A1D6" },
      },
      {
        name: "平均播放量",
        type: "line",
        yAxisIndex: 1,
        data: tagPlaySorted.map((t) => t.avg_play_count),
        smooth: true,
        symbol: "circle",
        symbolSize: 8,
        lineStyle: { color: "#ff7875", width: 2 },
        itemStyle: { color: "#ff7875" },
      },
    ],
  };

  const contribNames = upContributions.map((u) => u.up_nickname);
  const contribOption = {
    tooltip: {
      trigger: "axis" as const,
      axisPointer: { type: "shadow" as const },
    },
    legend: { data: ["视频数", "音频数", "图文数", "充电数"] },
    grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
    xAxis: {
      type: "category" as const,
      data: contribNames,
      axisLabel: { rotate: 30, interval: 0 },
    },
    yAxis: { type: "value" as const, name: "数量" },
    series: [
      {
        name: "视频数",
        type: "bar",
        stack: "贡献",
        data: upContributions.map((u) => u.video_count),
        itemStyle: { color: "#00A1D6" },
      },
      {
        name: "音频数",
        type: "bar",
        stack: "贡献",
        data: upContributions.map((u) => u.audio_count),
        itemStyle: { color: "#52c41a" },
      },
      {
        name: "图文数",
        type: "bar",
        stack: "贡献",
        data: upContributions.map((u) => u.image_text_count),
        itemStyle: { color: "#faad14" },
      },
      {
        name: "充电数",
        type: "bar",
        stack: "贡献",
        data: upContributions.map((u) => u.elec),
        itemStyle: { color: "#ff7875" },
      },
    ],
  };

  const interactionOption = {
    tooltip: { trigger: "item" as const, formatter: "{b}: {c} ({d}%)" },
    legend: { orient: "vertical" as const, right: 10, top: "center" },
    series: [
      {
        name: "互动结构",
        type: "pie",
        radius: ["40%", "70%"],
        center: ["40%", "50%"],
        data: interaction,
        emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: "rgba(0,0,0,0.5)" } },
        label: { formatter: "{b}: {d}%" },
      },
    ],
  };

  const partitionImpactOption = {
    tooltip: {
      trigger: "axis" as const,
      axisPointer: { type: "cross" as const },
    },
    legend: { data: ["平均播放量", "平均互动率"] },
    grid: { left: "3%", right: "4%", bottom: "15%", containLabel: true },
    xAxis: {
      type: "category" as const,
      data: partitionImpact.map((p) => p.partition),
      axisLabel: { rotate: 35, interval: 0 },
    },
    yAxis: [
      { type: "value" as const, name: "平均播放量", position: "left", axisLabel: { formatter: (v: number) => (v >= 10000 ? v / 10000 + "万" : String(v)) } },
      { type: "value" as const, name: "平均互动率", position: "right" },
    ],
    series: [
      {
        name: "平均播放量",
        type: "bar",
        yAxisIndex: 0,
        data: partitionImpact.map((p) => p.avg_play_count),
        itemStyle: { color: "#00A1D6" },
      },
      {
        name: "平均互动率",
        type: "line",
        yAxisIndex: 1,
        data: partitionImpact.map((p) => p.avg_interaction_rate),
        smooth: true,
        symbol: "circle",
        symbolSize: 8,
        lineStyle: { color: "#ff7875", width: 2 },
        itemStyle: { color: "#ff7875" },
      },
    ],
  };

  const durationImpactOption = {
    tooltip: {
      trigger: "axis" as const,
      axisPointer: { type: "cross" as const },
    },
    legend: { data: ["视频数", "平均播放量"] },
    grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
    xAxis: {
      type: "category" as const,
      data: durationImpact.map((d) => d.duration_bucket),
      axisLabel: { interval: 0 },
    },
    yAxis: [
      { type: "value" as const, name: "视频数", position: "left" },
      { type: "value" as const, name: "平均播放量", position: "right", axisLabel: { formatter: (v: number) => (v >= 10000 ? v / 10000 + "万" : String(v)) } },
    ],
    series: [
      {
        name: "视频数",
        type: "bar",
        yAxisIndex: 0,
        data: durationImpact.map((d) => d.video_count),
        itemStyle: { color: "#00A1D6" },
      },
      {
        name: "平均播放量",
        type: "line",
        yAxisIndex: 1,
        data: durationImpact.map((d) => d.avg_play_count),
        smooth: true,
        symbol: "circle",
        symbolSize: 8,
        lineStyle: { color: "#52c41a", width: 2 },
        itemStyle: { color: "#52c41a" },
      },
    ],
  };

  const weekLabels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
  const hourLabels = Array.from({ length: 24 }, (_, i) => `${i}:00`);
  const heatVideoData: [number, number, number][] = [];
  pubTimeHeat.forEach((h) => {
    heatVideoData.push([h.hour, h.weekday_idx, h.video_count]);
  });
  const pubTimeOption = {
    tooltip: {
      position: "top",
      formatter: (p: any) => {
        const item = pubTimeHeat.find(
          (h) => h.weekday_idx === p.value[1] && h.hour === p.value[0]
        );
        if (!item) return "";
        return `${weekLabels[p.value[1]]} ${hourLabels[p.value[0]]}<br/>视频数: ${item.video_count}<br/>平均播放: ${item.avg_play_count.toLocaleString()}`;
      },
    },
    grid: { left: "3%", right: "4%", top: "12%", bottom: "15%", containLabel: true },
    xAxis: { type: "category" as const, data: hourLabels, splitArea: { show: true } },
    yAxis: { type: "category" as const, data: weekLabels, splitArea: { show: true } },
    visualMap: {
      min: 0,
      max: Math.max(1, ...heatVideoData.map((d) => d[2])),
      calculable: true,
      orient: "horizontal" as const,
      left: "center",
      bottom: "2%",
      inRange: { color: ["#e0f3ff", "#00A1D6", "#fa541c"] },
    },
    series: [
      {
        name: "发布视频数",
        type: "heatmap",
        data: heatVideoData,
        emphasis: { itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.5)" } },
        label: { show: false },
      },
    ],
  };

  const contribColumns = [
    { title: "排名", render: (_: any, __: any, i: number) => i + 1, width: 60 },
    { title: "UP主昵称", dataIndex: "up_nickname", width: 150 },
    { title: "等级", dataIndex: "level", width: 60, render: (v: number) => `Lv${v}` },
    { title: "视频数", dataIndex: "video_count", width: 80, sorter: (a: any, b: any) => a.video_count - b.video_count },
    { title: "音频数", dataIndex: "audio_count", width: 80, sorter: (a: any, b: any) => a.audio_count - b.audio_count },
    { title: "图文数", dataIndex: "image_text_count", width: 80, sorter: (a: any, b: any) => a.image_text_count - b.image_text_count },
    { title: "充电数", dataIndex: "elec", width: 80, sorter: (a: any, b: any) => a.elec - b.elec },
    {
      title: "总贡献量",
      dataIndex: "total_contribution",
      width: 100,
      sorter: (a: any, b: any) => a.total_contribution - b.total_contribution,
      defaultSortOrder: "descend" as const,
      render: (v: number) => <strong style={{ color: "#00A1D6" }}>{v}</strong>,
    },
    {
      title: "粉丝数",
      dataIndex: "follower_count",
      render: (v: number) => (v >= 10000 ? (v / 10000).toFixed(1) + "万" : String(v)),
    },
  ];

  const upColumns = [
    { title: "排名", render: (_: any, __: any, i: number) => i + 1, width: 60 },
    { title: "UP主UID", dataIndex: "up_uid", width: 120 },
    { title: "UP主昵称", dataIndex: "up_nickname", width: 150 },
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
          <Card title="视频标签分布">
            <ReactECharts option={tagDistOption} style={{ height: 350 }} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="标签播放量分析 TOP20">
            <ReactECharts option={tagPlayOption} style={{ height: 350 }} />
          </Card>
        </Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="互动结构分布">
            <ReactECharts option={interactionOption} style={{ height: 350 }} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="分区传播力对比">
            <ReactECharts option={partitionImpactOption} style={{ height: 350 }} />
          </Card>
        </Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={24}>
          <Card title="UP主贡献量分析 TOP40">
            <ReactECharts option={contribOption} style={{ height: 400 }} />
          </Card>
        </Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="时长分布与传播力">
            <ReactECharts option={durationImpactOption} style={{ height: 350 }} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="发布时间规律">
            <ReactECharts option={pubTimeOption} style={{ height: 350 }} />
          </Card>
        </Col>
      </Row>
      <Row style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="UP主贡献明细 TOP20">
            <Table columns={contribColumns} dataSource={upContributions.slice(0, 20)} rowKey="up_uid" pagination={false} size="small" scroll={{ x: 900 }} />
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