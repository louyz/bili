import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu, Button, Dropdown, Avatar, Space } from "antd";
import {
  DashboardOutlined,
  BarChartOutlined,
  StarOutlined,
  SettingOutlined,
  LogoutOutlined,
  UserOutlined,
  FireOutlined,
  TrophyOutlined,
} from "@ant-design/icons";
import { useAuth } from "../contexts/AuthContext";

const { Header, Sider, Content } = Layout;

export default function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, isAdmin } = useAuth();

  const menuItems = [
    { key: "/", icon: <DashboardOutlined />, label: "仪表盘" },
    { key: "/ranking", icon: <TrophyOutlined />, label: "热门排行" },
    { key: "/analysis", icon: <BarChartOutlined />, label: "数据分析" },
    { key: "/favorites", icon: <StarOutlined />, label: "我的收藏" },
    ...(isAdmin
      ? [{ key: "/admin", icon: <SettingOutlined />, label: "管理后台" }]
      : []),
  ];

  const userMenu = {
    items: [
      { key: "info", icon: <UserOutlined />, label: `${user?.nickname || user?.username}` },
      { type: "divider" as const },
      {
        key: "logout",
        icon: <LogoutOutlined />,
        label: "退出登录",
        onClick: () => {
          logout();
          navigate("/login");
        },
      },
    ],
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        breakpoint="lg"
        collapsedWidth="60"
        width={200}
        style={{ background: "#001529" }}
      >
        <div
          style={{
            height: 64,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            borderBottom: "1px solid rgba(255,255,255,0.1)",
            cursor: "pointer",
          }}
          onClick={() => navigate("/")}
        >
          <FireOutlined style={{ fontSize: 24, color: "#00A1D6" }} />
          <span
            style={{
              marginLeft: 8,
              fontSize: 16,
              fontWeight: 700,
              color: "#fff",
              whiteSpace: "nowrap",
            }}
          >
            B站热门分析
          </span>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0, marginTop: 8 }}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: "#001529",
            padding: "0 24px",
            display: "flex",
            justifyContent: "flex-end",
            alignItems: "center",
            borderBottom: "1px solid rgba(255,255,255,0.1)",
            height: 64,
          }}
        >
          <Space>
            <Dropdown menu={userMenu} placement="bottomRight">
              <Button type="text" style={{ height: 48, color: "rgba(255,255,255,0.85)" }}>
                <Space>
                  <Avatar size="small" icon={<UserOutlined />} />
                  <span>{user?.nickname || user?.username}</span>
                </Space>
              </Button>
            </Dropdown>
          </Space>
        </Header>
        <Content
          style={{
            margin: 16,
            padding: 24,
            background: "#fff",
            borderRadius: 8,
            minHeight: 280,
            overflow: "auto",
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}