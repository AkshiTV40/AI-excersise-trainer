import React from 'react';

function ExerciseFeedback({ analysis }) {
  if (!analysis) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Exercise Feedback</h3>
        <p className="text-gray-500 text-sm">Start tracking to see exercise feedback</p>
      </div>
    );
  }

  const { exercise, rep_count, state, angles, form_issues, feedback } = analysis;

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Exercise Feedback</h3>
      
      {/* Exercise Info */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Exercise</span>
          <span className="text-sm font-semibold text-gray-900 capitalize">
            {exercise.replace('_', ' ')}
          </span>
        </div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Reps</span>
          <span className="text-2xl font-bold text-primary-600">{rep_count}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">State</span>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            state === 'start' ? 'bg-green-100 text-green-800' :
            state === 'end' ? 'bg-blue-100 text-blue-800' :
            'bg-yellow-100 text-yellow-800'
          }`}>
            {state}
          </span>
        </div>
      </div>

      {/* Angles */}
      {angles && Object.keys(angles).length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Joint Angles</h4>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(angles).map(([key, value]) => (
              <div key={key} className="bg-gray-50 rounded p-2">
                <div className="text-xs text-gray-500 capitalize">{key.replace('_', ' ')}</div>
                <div className="text-lg font-semibold text-gray-900">
                  {Math.round(value)}°
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Feedback Messages */}
      {feedback && feedback.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Feedback</h4>
          <div className="space-y-2">
            {feedback.map((msg, idx) => (
              <div key={idx} className="text-sm text-gray-700 bg-gray-50 rounded p-2">
                {msg}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Form Issues */}
      {form_issues && form_issues.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Form Issues</h4>
          <div className="space-y-2">
            {form_issues.map((issue, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg ${
                  issue.severity === 'critical' ? 'bg-red-50 border border-red-200' :
                  issue.severity === 'warning' ? 'bg-yellow-50 border border-yellow-200' :
                  'bg-blue-50 border border-blue-200'
                }`}
              >
                <div className="flex items-start">
                  <div className={`mr-2 mt-0.5 ${
                    issue.severity === 'critical' ? 'text-red-500' :
                    issue.severity === 'warning' ? 'text-yellow-500' :
                    'text-blue-500'
                  }`}>
                    {issue.severity === 'critical' && '⚠️'}
                    {issue.severity === 'warning' && '⚡'}
                    {issue.severity === 'info' && 'ℹ️'}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{issue.message}</p>
                    <p className="text-xs text-gray-600 mt-1">{issue.suggestion}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ExerciseFeedback;
