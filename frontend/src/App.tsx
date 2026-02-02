import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Recommend from './pages/Recommend';
import Query from './pages/Query';
import Tagging from './pages/Tagging';
import Analyze from './pages/Analyze';

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
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
