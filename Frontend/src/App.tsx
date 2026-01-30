import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard';
import Devices from './pages/Devices';
import PowerAnalysis from './pages/PowerAnalysis';
import Schedule from './pages/Schedule';
import Alerts from './pages/Alerts';
import Settings from './pages/Settings';
import ApiLogs from './pages/ApiLogs';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/devices" element={<Devices />} />
          <Route path="/power" element={<PowerAnalysis />} />
          <Route path="/schedule" element={<Schedule />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/api-logs" element={<ApiLogs />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
