import React from 'react';
import { motion } from 'framer-motion';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const TrackingStats = ({ stats }) => {
  const statItems = [
    {
      label: 'Frames Processed',
      value: stats.frameCount,
      icon: '📊',
      color: 'bg-gradient-to-br from-blue-500 to-blue-600'
    },
    {
      label: 'Active Tracks',
      value: stats.trackCount,
      icon: '👥',
      color: 'bg-gradient-to-br from-green-500 to-green-600'
    },
    {
      label: 'Inference Time',
      value: `${(stats.inferenceTime * 1000).toFixed(0)}ms`,
      icon: '⚡',
      color: 'bg-gradient-to-br from-purple-500 to-purple-600'
    },
    {
      label: 'FPS',
      value: stats.fps.toFixed(1),
      icon: '🎯',
      color: 'bg-gradient-to-br from-orange-500 to-orange-600'
    }
  ];

  // Performance chart data
  const chartData = {
    labels: ['0', '1', '2', '3', '4', '5'],
    datasets: [
      {
        label: 'FPS',
        data: [30, 28, 32, 29, 31, 30],
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5
      },
      {
        label: 'Inference Time (ms)',
        data: [95, 92, 88, 90, 87, 91],
        borderColor: '#8b5cf6',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        fill: true,
        tension: 0.4,
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          usePointStyle: true,
          padding: 15,
          font: {
            size: 12,
            weight: '500'
          }
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        titleFont: {
          size: 14,
          weight: '600'
        },
        bodyFont: {
          size: 13
        },
        cornerRadius: 8
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
          drawBorder: false
        },
        ticks: {
          font: {
            size: 11
          }
        }
      },
      x: {
        grid: {
          display: false,
          drawBorder: false
        },
        ticks: {
          font: {
            size: 11
          }
        }
      }
    }
  };

  return (
    <motion.div 
      className="card card-hover"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.3 }}
    >
      <h2 className="text-xl font-bold text-gray-900 mb-6 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
        Statistics
      </h2>
      
      <div className="grid grid-cols-2 gap-4 mb-8">
        {statItems.map((item, index) => (
          <motion.div 
            key={index}
            className="stat-card"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.4 + index * 0.1 }}
            whileHover={{ scale: 1.05, rotate: 1 }}
          >
            <div className="flex items-center space-x-3">
              <motion.div 
                className={`${item.color} text-white p-3 rounded-xl shadow-lg`}
                whileHover={{ scale: 1.1, rotate: 5 }}
                transition={{ type: "spring", stiffness: 400 }}
              >
                <div className="text-xl">{item.icon}</div>
              </motion.div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{item.value}</p>
                <p className="text-sm text-gray-600">{item.label}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Performance Chart */}
      <motion.div 
        className="bg-gradient-to-br from-white to-gray-50 rounded-xl p-4 shadow-md"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.6 }}
      >
        <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center space-x-2">
          <span>📈</span>
          <span>Performance Metrics</span>
        </h3>
        <div className="h-48">
          <Line data={chartData} options={chartOptions} />
        </div>
      </motion.div>

      {/* System Status */}
      <motion.div 
        className="mt-6 bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.7 }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm font-semibold text-gray-800">System Status</span>
          </div>
          <span className="text-sm font-medium text-green-600">Optimal</span>
        </div>
        <div className="mt-2 text-xs text-gray-600">
          AI Model: YOLOv8 • Detection Mode: Real-time • Processing: Normal
        </div>
      </motion.div>
    </motion.div>
  );
};

export default TrackingStats;