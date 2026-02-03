import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Recommend from './pages/Recommend';
import Query from './pages/Query';
import Tagging from './pages/Tagging';
import Analyze from './pages/Analyze';
import Settings from './pages/Settings';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/recommend" element={<Recommend />} />
          <Route path="/query" element={<Query />} />
          <Route path="/tagging" element={<Tagging />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
