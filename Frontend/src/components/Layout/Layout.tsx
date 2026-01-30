import { Outlet } from 'react-router-dom';
import TopBar from './TopBar';
import Sidebar from './Sidebar';

export default function Layout() {
  return (
    <div className="h-screen w-screen overflow-hidden">
      <TopBar />
      <Sidebar />
      <main className="ml-[250px] mt-[60px] h-[calc(100vh-60px)] overflow-y-auto overflow-x-hidden bg-[#0f172a] p-4 sm:p-6">
        <div className="h-[calc(100vh-60px-2rem)] sm:h-[calc(100vh-60px-3rem)]">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
