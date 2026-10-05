import { BrowserRouter, Routes, Route } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import Dashboard from './pages/Dashboard'
import DatasetPage from './pages/DatasetPage'
import OptimizationConfig from './pages/OptimizationConfig'
import OptimizationRunning from './pages/OptimizationRunning'
import Results from './pages/Results'
import Prediction from './pages/Prediction'
import HistoryPage from './pages/HistoryPage'
import DocsPage from './pages/DocsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dataset" element={<DatasetPage />} />
          <Route path="/optimization" element={<OptimizationConfig />} />
          <Route path="/optimization/run/:id" element={<OptimizationRunning />} />
          <Route path="/results" element={<Results />} />
          <Route path="/results/:id" element={<Results />} />
          <Route path="/prediction" element={<Prediction />} />
          <Route path="/prediction/:id" element={<Prediction />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/docs" element={<DocsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
