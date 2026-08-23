import { useEffect, useState } from "react";
import { Card, Table, Button, Tabs, Tag, message, Space, Popconfirm, Statistic, Row, Col } from "antd";
import { ReloadOutlined, PlayCircleOutlined, CheckCircleOutlined, CloseCircleOutlined } from "@ant-design/icons";
import { adminApi, type CrawlLog } from "../api";

export default function AdminPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [userTotal, setUserTotal] = useState(0);
  const [userPage, setUserPage] = useState(1);
  const [logs, setLogs] = useState<CrawlLog[]>([]);
  const [logTotal, setLogTotal] = useState(0);
  const [logPage, setLogPage] = useState(1);
  const [crawlStatus, setCrawlStatus] = useState<any>({});
  const [loading, setLoading] = useState(false);

  const fetchUsers = async () => {
    const res = await adminApi.getUsers({ page: userPage, page_size: 20 });
    setUsers(res.data.items);
    setUserTotal(res.data.total);
  };

  const fetchLogs = async () => {
    const res = await adminApi.getCrawlLogs({ page: logPage, page_size: 20 });
    setLogs(res.data.items);
    setLogTotal(res.data.total);
  };

  const fetchStatus = async () => {
    const res = await adminApi.getCrawlStatus();
    setCrawlStatus(res.data);
  };

  useEffect(() => {
    fetchUsers();
    fetchLogs();
    fetchStatus();
  }, [userPage, logPage]);

  const toggleUser = async (id: number) => {
    await adminApi.toggleUserActive(id);
    message.success("状态已更新");
    fetchUsers();
  };

  const triggerCrawl = async () => {
    try {
      await adminApi.triggerCrawl("popular");
      message.success("爬虫任务已触发");
      setTimeout(fetchStatus, 2000);
      setTimeout(fetchLogs, 3000);
    } catch (err: any) {
      message.error(err.response?.data?.detail || "触发失败");
    }
  };

  const userColumns = [
    { title: "ID", dataIndex: "id", width: 60 },
    { title: "用户名", dataIndex: "username", width: 120 },
    { title: "邮箱", dataIndex: "email", width: 200 },
    { title: "昵称", dataIndex: "nickname", width: 120 },
    {
      title: "角色",
      dataIndex: "role",
      width: 80,
      render: (v: string) => <Tag color={v === "admin" ? "red" : "blue"}>{v}</Tag>,
    },
    {
      title: "状态",
      dataIndex: "is_active",
      width: 80,
      render: (v: boolean) => (v ? <Tag color="green">正常</Tag> : <Tag color="gray">禁用</Tag>),
    },
    {
      title: "注册时间",
      dataIndex: "created_at",
      width: 180,
      render: (v: string) => new Date(v).toLocaleString(),
    },
    {
      title: "操作",
      width: 80,
      render: (_: any, r: any) => (
        <Popconfirm title={`确定${r.is_active ? "禁用" : "启用"}该用户？`} onConfirm={() => toggleUser(r.id)}>
          <Button type="link" danger={r.is_active}>
            {r.is_active ? "禁用" : "启用"}
          </Button>
        </Popconfirm>
      ),
    },
  ];

  const logColumns = [
    { title: "ID", dataIndex: "id", width: 60 },
    {
      title: "类型",
      dataIndex: "task_type",
      width: 100,
      render: (v: string) => <Tag>{v}</Tag>,
    },
    {
      title: "状态",
      dataIndex: "status",
      width: 80,
      render: (v: string) => {
        const colors: Record<string, string> = { success: "green", failed: "red", running: "blue", partial: "orange" };
        return <Tag color={colors[v] || "default"}>{v}</Tag>;
      },
    },
    { title: "总数", dataIndex: "total_videos", width: 60 },
    { title: "成功", dataIndex: "success_count", width: 60 },
    { title: "失败", dataIndex: "failed_count", width: 60 },
    {
      title: "耗时",
      dataIndex: "duration_ms",
      width: 80,
      render: (v: number) => v ? `${(v / 1000).toFixed(1)}s` : "-",
    },
    {
      title: "开始时间",
      dataIndex: "started_at",
      width: 180,
      render: (v: string) => v ? new Date(v).toLocaleString() : "-",
    },
    {
      title: "错误",
      dataIndex: "error_msg",
      ellipsis: true,
      width: 200,
      render: (v: string) => v || "-",
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>管理后台</h2>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="爬虫状态" value={crawlStatus.running ? "运行中" : "空闲"} valueStyle={{ color: crawlStatus.running ? "#1890ff" : "#52c41a" }} />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div>
                <strong>进度: </strong>{crawlStatus.progress || "0/0"}
                <br />
                <span style={{ color: "#666" }}>{crawlStatus.message || "空闲中"}</span>
              </div>
              <Space>
                <Button icon={<ReloadOutlined />} onClick={fetchStatus}>刷新</Button>
                <Button type="primary" icon={<PlayCircleOutlined />} onClick={triggerCrawl} loading={crawlStatus.running}>
                  触发爬虫
                </Button>
              </Space>
            </div>
          </Card>
        </Col>
      </Row>
      <Tabs
        items={[
          {
            key: "users",
            label: "用户管理",
            children: (
              <Table
                columns={userColumns}
                dataSource={users}
                rowKey="id"
                pagination={{
                  current: userPage,
                  total: userTotal,
                  pageSize: 20,
                  showTotal: (t) => `共 ${t} 条`,
                  onChange: (p) => setUserPage(p),
                }}
                size="small"
              />
            ),
          },
          {
            key: "logs",
            label: "爬虫日志",
            children: (
              <Table
                columns={logColumns}
                dataSource={logs}
                rowKey="id"
                pagination={{
                  current: logPage,
                  total: logTotal,
                  pageSize: 20,
                  showTotal: (t) => `共 ${t} 条`,
                  onChange: (p) => setLogPage(p),
                }}
                size="small"
                scroll={{ x: 1000 }}
              />
            ),
          },
        ]}
      />
    </div>
  );
}