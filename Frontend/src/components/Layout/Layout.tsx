import { Outlet } from 'react-router-dom';
import TopBar from './TopBar';
import Sidebar from './Sidebar';

export default function Layout() {
  return (
    <div className="h-screen w-screen overflow-hidden">
      <TopBar />
      <Sidebar />
      <main className="fixed top-[60px] left-[250px] right-0 bottom-0 bg-[#0f172a] p-4 overflow-y-auto overflow-x-hidden">
        <Outlet />
      </main>
    </div>
  );
}
