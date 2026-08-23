import { useEffect, useState } from "react";
import { Card, Table, Button, Modal, Input, Select, message, Space, Tag, Popconfirm } from "antd";
import { PlusOutlined, DeleteOutlined, FolderOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { favApi } from "../api";

export default function FavoritesPage() {
  const [folders, setFolders] = useState<any[]>([]);
  const [videos, setVideos] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [folderId, setFolderId] = useState<number | undefined>();
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [newFolderDesc, setNewFolderDesc] = useState("");
  const navigate = useNavigate();

  const fetchFolders = async () => {
    const res = await favApi.getFolders();
    setFolders(res.data);
  };

  const fetchVideos = async () => {
    setLoading(true);
    try {
      const res = await favApi.getVideos({ folder_id: folderId, page, page_size: 20 });
      setVideos(res.data.items);
      setTotal(res.data.total);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFolders();
  }, []);

  useEffect(() => {
    fetchVideos();
  }, [folderId, page]);

  const createFolder = async () => {
    if (!newFolderName.trim()) return;
    await favApi.createFolder(newFolderName, newFolderDesc);
    message.success("创建成功");
    setModalOpen(false);
    setNewFolderName("");
    setNewFolderDesc("");
    fetchFolders();
  };

  const deleteFolder = async (id: number) => {
    await favApi.deleteFolder(id);
    message.success("删除成功");
    if (folderId === id) setFolderId(undefined);
    fetchFolders();
  };

  const removeVideo = async (bvid: string) => {
    await favApi.removeVideo(bvid, folderId);
    message.success("已取消收藏");
    fetchVideos();
  };

  const columns = [
    { title: "#", render: (_: any, __: any, i: number) => (page - 1) * 20 + i + 1, width: 50 },
    {
      title: "标题",
      dataIndex: "title",
      ellipsis: true,
      render: (t: string, r: any) => (
        <a onClick={() => navigate(`/detail/${r.bvid}`)}>{t}</a>
      ),
    },
    {
      title: "播放量",
      dataIndex: "play_count",
      width: 100,
      render: (v: number) => (v / 10000).toFixed(1) + "万",
    },
    {
      title: "热度",
      dataIndex: "heat_score",
      width: 100,
      render: (v: number) => (
        <Tag color="orange">{(v / 10000).toFixed(1)}万</Tag>
      ),
    },
    {
      title: "备注",
      dataIndex: "note",
      width: 150,
      ellipsis: true,
      render: (v: string) => v || "-",
    },
    {
      title: "收藏时间",
      dataIndex: "created_at",
      width: 180,
      render: (v: string) => new Date(v).toLocaleString(),
    },
    {
      title: "操作",
      width: 80,
      render: (_: any, r: any) => (
        <Popconfirm title="确定取消收藏？" onConfirm={() => removeVideo(r.bvid)}>
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <h2>我的收藏</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          新建收藏夹
        </Button>
      </div>
      <Space wrap style={{ marginBottom: 16 }}>
        <Button
          type={!folderId ? "primary" : "default"}
          onClick={() => { setFolderId(undefined); setPage(1); }}
        >
          全部
        </Button>
        {folders.map((f) => (
          <Button
            key={f.id}
            type={folderId === f.id ? "primary" : "default"}
            onClick={() => { setFolderId(f.id); setPage(1); }}
          >
            <FolderOutlined /> {f.name} ({f.video_count || 0})
          </Button>
        ))}
        {folders.some((f) => f.id === folderId) && folderId && (
          <Popconfirm title="确定删除此收藏夹？" onConfirm={() => deleteFolder(folderId)}>
            <Button danger icon={<DeleteOutlined />}>
              删除当前收藏夹
            </Button>
          </Popconfirm>
        )}
      </Space>
      <Table
        columns={columns}
        dataSource={videos}
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
      />
      <Modal
        title="新建收藏夹"
        open={modalOpen}
        onOk={createFolder}
        onCancel={() => setModalOpen(false)}
      >
        <Input
          placeholder="收藏夹名称"
          value={newFolderName}
          onChange={(e) => setNewFolderName(e.target.value)}
          style={{ marginBottom: 12 }}
        />
        <Input
          placeholder="描述（可选）"
          value={newFolderDesc}
          onChange={(e) => setNewFolderDesc(e.target.value)}
        />
      </Modal>
    </div>
  );
}