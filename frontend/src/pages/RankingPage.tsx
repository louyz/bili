import { useEffect, useState } from "react";
import { Table, Input, Select, Tag, Space, Button, Image, Typography, message } from "antd";
import { SearchOutlined, StarOutlined, StarFilled } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { videoApi, favApi, type VideoItem } from "../api";
import { proxyImage } from "../utils/proxy";

const { Text } = Typography;

const SORT_OPTIONS = [
  { value: "heat_score", label: "综合热度" },
  { value: "play_count", label: "播放量" },
  { value: "like_count", label: "点赞数" },
  { value: "comment_count", label: "评论数" },
  { value: "pub_time", label: "发布时间" },
];

export default function RankingPage() {
  const [data, setData] = useState<VideoItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState("heat_score");
  const [partition, setPartition] = useState<string | undefined>();
  const [keyword, setKeyword] = useState("");
  const [partitions, setPartitions] = useState<string[]>([]);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const navigate = useNavigate();

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await videoApi.getRanking({ page, page_size: 20, sort_by: sortBy, partition, keyword });
      setData(res.data.items);
      setTotal(res.data.total);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    videoApi.getPartitions().then((res) => {
      setPartitions(res.data.map((p: any) => p.name));
    });
  }, []);

  useEffect(() => {
    fetchData();
  }, [page, sortBy, partition, keyword]);

  const toggleFavorite = async (bvid: string) => {
    try {
      if (favorites.has(bvid)) {
        await favApi.removeVideo(bvid);
        setFavorites((prev) => {
          const next = new Set(prev);
          next.delete(bvid);
          return next;
        });
        message.success("已取消收藏");
      } else {
        await favApi.addVideo(bvid);
        setFavorites((prev) => new Set(prev).add(bvid));
        message.success("收藏成功");
      }
    } catch (err: any) {
      message.error(err.response?.data?.detail || "操作失败");
    }
  };

  const formatNum = (n: number) => {
    if (n >= 10000) return (n / 10000).toFixed(1) + "万";
    return String(n);
  };

  const formatDuration = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${String(sec).padStart(2, "0")}`;
  };

  const columns = [
    {
      title: "#",
      width: 50,
      render: (_: any, __: any, i: number) => (page - 1) * 20 + i + 1,
    },
    {
      title: "封面",
      width: 130,
      render: (_: any, r: VideoItem) => (
        <Image
          src={proxyImage(r.cover_url)}
          width={110}
          height={65}
          style={{ borderRadius: 4, objectFit: "cover", cursor: "pointer" }}
          preview={false}
          onClick={() => navigate(`/detail/${r.bvid}`)}
        />
      ),
    },
    {
      title: "标题",
      dataIndex: "title",
      ellipsis: true,
      render: (t: string, r: VideoItem) => (
        <a onClick={() => navigate(`/detail/${r.bvid}`)} style={{ fontWeight: 500 }}>
          {t}
        </a>
      ),
    },
    {
      title: "分区",
      dataIndex: "partition_main",
      width: 100,
      render: (t: string) => <Tag color="blue">{t}</Tag>,
    },
    {
      title: "播放量",
      dataIndex: "play_count",
      width: 100,
      sorter: true,
      render: (n: number) => <Text strong>{formatNum(n)}</Text>,
    },
    {
      title: "点赞",
      dataIndex: "like_count",
      width: 80,
      render: (n: number) => formatNum(n),
    },
    {
      title: "评论",
      dataIndex: "comment_count",
      width: 80,
      render: (n: number) => formatNum(n),
    },
    {
      title: "时长",
      dataIndex: "duration",
      width: 70,
      render: (n: number) => formatDuration(n),
    },
    {
      title: "UP主",
      dataIndex: "up_nickname",
      width: 120,
      ellipsis: true,
    },
    {
      title: "热度",
      dataIndex: "heat_score",
      width: 100,
      render: (n: number) => (
        <Tag color={n > 500000 ? "red" : n > 200000 ? "orange" : "default"}>
          {(n / 10000).toFixed(1)}万
        </Tag>
      ),
    },
    {
      title: "收藏",
      width: 60,
      render: (_: any, r: VideoItem) => (
        <Button
          type="text"
          icon={favorites.has(r.bvid) ? <StarFilled style={{ color: "#faad14" }} /> : <StarOutlined />}
          onClick={() => toggleFavorite(r.bvid)}
        />
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>热门视频排行</h2>
      <Space style={{ marginBottom: 16 }} wrap>
        <Input
          prefix={<SearchOutlined />}
          placeholder="搜索标题..."
          value={keyword}
          onChange={(e) => {
            setKeyword(e.target.value);
            setPage(1);
          }}
          style={{ width: 250 }}
          allowClear
        />
        <Select
          value={sortBy}
          onChange={(v) => { setSortBy(v); setPage(1); }}
          options={SORT_OPTIONS}
          style={{ width: 140 }}
        />
        <Select
          value={partition}
          onChange={(v) => { setPartition(v); setPage(1); }}
          placeholder="全部分区"
          allowClear
          options={partitions.map((p) => ({ value: p, label: p }))}
          style={{ width: 150 }}
        />
      </Space>
      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          total,
          pageSize: 20,
          showTotal: (t) => `共 ${t} 条`,
          onChange: (p) => setPage(p),
        }}
        size="middle"
        scroll={{ x: 1200 }}
      />
    </div>
  );
}