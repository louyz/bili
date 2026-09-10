import { useEffect, useState, useRef } from "react";
import { Card, Table, Button, Tabs, Tag, message, Space, Popconfirm, Statistic, Row, Col, Modal, Form, Input, Switch } from "antd";
import { ReloadOutlined, PlayCircleOutlined, StopOutlined, PlusOutlined, EditOutlined, KeyOutlined } from "@ant-design/icons";
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


  const [userModalOpen, setUserModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<any>(null);
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);
  const [passwordUserId, setPasswordUserId] = useState<number | null>(null);
  const [userForm] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

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

  const openCreateModal = () => {
    setEditingUser(null);
    userForm.resetFields();
    setUserModalOpen(true);
  };

  const openEditModal = (user: any) => {
    setEditingUser(user);
    userForm.setFieldsValue({
      email: user.email,
      nickname: user.nickname,
      role: user.role,
      is_active: user.is_active,
    });
    setUserModalOpen(true);
  };

  const handleUserSubmit = async () => {
    try {
      const values = await userForm.validateFields();
      if (editingUser) {
        await adminApi.updateUser(editingUser.id, values);
        message.success("用户信息已更新");
      } else {
        await adminApi.createUser({ ...values, role: "user" });
        message.success("用户创建成功");
      }
      setUserModalOpen(false);
      fetchUsers();
    } catch (err: any) {
      if (err.response) {
        message.error(err.response.data?.detail || "操作失败");
      }
    }
  };

  const openPasswordModal = (userId: number) => {
    setPasswordUserId(userId);
    passwordForm.resetFields();
    setPasswordModalOpen(true);
  };

  const handlePasswordReset = async () => {
    try {
      const values = await passwordForm.validateFields();
      await adminApi.resetUserPassword(passwordUserId!, values.new_password);
      message.success("密码已重置");
      setPasswordModalOpen(false);
    } catch (err: any) {
      if (err.response) {
        message.error(err.response.data?.detail || "操作失败");
      }
    }
  };

  const startPolling = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      await fetchStatus();
      await fetchLogs();
    }, 3000);
  };

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  useEffect(() => {
    return () => stopPolling();
  }, []);

  const triggerCrawl = async () => {
    try {
      const res = await adminApi.triggerCrawl("full_sync");
      message.success(res.data.message || "爬虫任务已触发");
      await fetchStatus();
      startPolling();
    } catch (err: any) {
      message.error(err.response?.data?.detail || "触发失败");
    }
  };

  const stopCrawl = async () => {
    try {
      await adminApi.stopCrawl();
      message.success("停止指令已发送");
      await fetchStatus();
    } catch (err: any) {
      message.error(err.response?.data?.detail || "停止失败");
    }
  };

  useEffect(() => {
    if (crawlStatus.running) {
      startPolling();
    } else {
      stopPolling();
    }
  }, [crawlStatus.running]);

  const userColumns = [
    { title: "ID", dataIndex: "id", width: 60 },
    { title: "用户名", dataIndex: "username", width: 120 },
    { title: "邮箱", dataIndex: "email", width: 200 },
    { title: "昵称", dataIndex: "nickname", width: 120 },
    {
      title: "角色",
      dataIndex: "role",
      width: 80,
      render: (v: string) => <Tag color={v === "admin" ? "red" : "blue"}>{v === "admin" ? "管理员" : "用户"}</Tag>,
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
      width: 240,
      render: (_: any, r: any) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEditModal(r)}>
            编辑
          </Button>
          <Button type="link" size="small" icon={<KeyOutlined />} onClick={() => openPasswordModal(r.id)}>
            重置密码
          </Button>
          {r.role !== "admin" && (
            <Popconfirm title={`确定${r.is_active ? "禁用" : "启用"}该用户？`} onConfirm={() => toggleUser(r.id)}>
              <Button type="link" size="small" danger={r.is_active}>
                {r.is_active ? "禁用" : "启用"}
              </Button>
            </Popconfirm>
          )}
        </Space>
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
                <Button danger icon={<StopOutlined />} onClick={stopCrawl} disabled={!crawlStatus.running}>
                  停止爬虫
                </Button>
              </Space>
            </div>
          </Card>
        </Col>
      </Row>
      <Tabs
        onChange={(key) => {
          if (key === "users") fetchUsers();
          else if (key === "logs") fetchLogs();
        }}
        items={[
          {
            key: "users",
            label: "用户管理",
            children: (
              <>
                <div style={{ marginBottom: 12 }}>
                  <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
                    新增用户
                  </Button>
                </div>
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
              </>
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

      <Modal
        title={editingUser ? "编辑用户" : "新增用户"}
        open={userModalOpen}
        onOk={handleUserSubmit}
        onCancel={() => setUserModalOpen(false)}
        destroyOnClose
      >
        <Form form={userForm} layout="vertical" style={{ marginTop: 16 }}>
          {!editingUser && (
            <>
              <Form.Item name="username" label="用户名" rules={[{ required: true, min: 3, max: 50, message: "用户名 3-50 个字符" }]}>
                <Input placeholder="登录用户名" />
              </Form.Item>
              <Form.Item name="password" label="密码" rules={[{ required: true, min: 6, max: 50, message: "密码 6-50 个字符" }]}>
                <Input.Password placeholder="登录密码" />
              </Form.Item>
            </>
          )}
          <Form.Item name="email" label="邮箱" rules={[{ type: "email", message: "请输入有效邮箱" }]}>
            <Input placeholder="邮箱地址" />
          </Form.Item>
          <Form.Item name="nickname" label="昵称">
            <Input placeholder="显示昵称" />
          </Form.Item>
          {editingUser && editingUser.role !== "admin" && (
            <Form.Item name="is_active" label="启用状态" valuePropName="checked">
              <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            </Form.Item>
          )}
        </Form>
      </Modal>

      <Modal
        title="重置密码"
        open={passwordModalOpen}
        onOk={handlePasswordReset}
        onCancel={() => setPasswordModalOpen(false)}
        destroyOnClose
      >
        <Form form={passwordForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="new_password" label="新密码" rules={[{ required: true, min: 6, max: 50, message: "密码 6-50 个字符" }]}>
            <Input.Password placeholder="请输入新密码" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}