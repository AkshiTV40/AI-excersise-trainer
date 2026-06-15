import React from 'react';

const TrackList = ({ tracks }) => {
  const mockTracks = [
    { id: 1, confidence: 0.95, duration: '12s', status: 'active' },
    { id: 2, confidence: 0.87, duration: '8s', status: 'active' },
    { id: 3, confidence: 0.92, duration: '15s', status: 'active' },
  ];

  const displayTracks = tracks.length > 0 ? tracks : mockTracks;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Active Tracks</h2>
        <span className="bg-primary-100 text-primary-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
          {displayTracks.length}
        </span>
      </div>

      {displayTracks.length === 0 ? (
        <div className="text-center py-8 text-gray-400">
          <svg className="w-12 h-12 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <p className="text-sm">No active tracks</p>
          <p className="text-xs mt-1">Start tracking to see detected persons</p>
        </div>
      ) : (
        <div className="space-y-3">
          {displayTracks.map((track) => (
            <div
              key={track.id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="text-primary-700 font-semibold text-sm">
                    #{track.id}
                  </span>
                </div>
                <div>
                  <p className="font-medium text-gray-900">Person {track.id}</p>
                  <p className="text-sm text-gray-500">Duration: {track.duration}</p>
                </div>
              </div>
              <div className="text-right">
                <div className="flex items-center space-x-1">
                  <div className={`w-2 h-2 rounded-full ${
                    track.status === 'active' ? 'bg-green-500' : 'bg-gray-400'
                  }`} />
                  <span className="text-xs text-gray-500 capitalize">{track.status}</span>
                </div>
                <p className="text-sm font-medium text-gray-900 mt-1">
                  {(track.confidence * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Track History */}
      {displayTracks.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Recent Activity</h3>
          <div className="space-y-2">
            <div className="flex items-center text-sm text-gray-600">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2" />
              <span>Person #1 entered frame</span>
              <span className="ml-auto text-xs text-gray-400">2s ago</span>
            </div>
            <div className="flex items-center text-sm text-gray-600">
              <div className="w-2 h-2 bg-blue-500 rounded-full mr-2" />
              <span>Person #2 detected</span>
              <span className="ml-auto text-xs text-gray-400">5s ago</span>
            </div>
            <div className="flex items-center text-sm text-gray-600">
              <div className="w-2 h-2 bg-purple-500 rounded-full mr-2" />
              <span>Person #3 tracking started</span>
              <span className="ml-auto text-xs text-gray-400">8s ago</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TrackList;