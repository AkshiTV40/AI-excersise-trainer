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

  const { exercise, rep_count, state, angles, form_issues, feedback, ai_guidance, guidance, summary } = analysis;
  const formScore = analysis.form_score ?? analysis.formScore;
  const issueList = form_issues || [];
  const feedbackList = feedback || [];

  const getScoreStatus = (score) => {
    if (score === undefined || score === null || Number.isNaN(Number(score))) return 'No score yet';
    const value = Number(score);
    if (value >= 85) return 'Excellent';
    if (value >= 70) return 'Good';
    if (value >= 50) return 'Needs Improvement';
    return 'Needs Major Correction';
  };

  const getImprovementPlan = () => {
    const exerciseName = (exercise || 'exercise').toLowerCase();
    const issueText = issueList.map(issue => issue.message || '').join(' ').toLowerCase();
    const suggestions = issueList.map(issue => issue.suggestion).filter(Boolean);

    if (suggestions.length > 0) {
      return suggestions.slice(0, 2);
    }

    if (exerciseName.includes('squat')) {
      return [
        'Keep your chest tall and brace your core before each rep.',
        'Track your knees in the same direction as your toes.',
        'Use a depth you can control without your heels lifting.',
        'Pause briefly at the bottom, then drive through the whole foot.'
      ];
    }

    if (exerciseName.includes('push')) {
      return [
        'Keep your body in a straight line from head to heels.',
        'Lower with control instead of dropping quickly.',
        'Press evenly through both hands.',
        'Keep the neck neutral and avoid shrugging.'
      ];
    }

    if (exerciseName.includes('lunge')) {
      return [
        'Step far enough for both knees to bend close to 90 degrees.',
        'Keep your front heel down and torso tall.',
        'Push through the front foot to return to the start.',
        'Keep hips square and avoid twisting.'
      ];
    }

    if (exerciseName.includes('plank')) {
      return [
        'Keep shoulders stacked over elbows and hips level.',
        'Brace your abs instead of letting the hips sag.',
        'Use shorter clean holds instead of long poor holds.',
        'Breathe steadily and reset posture between holds.'
      ];
    }

    if (exerciseName.includes('dead')) {
      return [
        'Keep the load close to your body.',
        'Hinge from the hips with a neutral spine.',
        'Drive through the floor and stand tall without leaning back.',
        'Use lighter weight until the hip hinge is consistent.'
      ];
    }

    return [
      'Move through a controlled range of motion.',
      'Keep joints aligned and avoid sudden jerky movement.',
      'Reset posture between reps.',
      'Stop if pain appears or form breaks down.'
    ];
  };

  const getAngleNotes = () => {
    if (!angles || Object.keys(angles).length === 0) return [];

    const notes = [];
    const leftKnee = angles.leftKnee ?? angles.left_knee;
    const rightKnee = angles.rightKnee ?? angles.right_knee;
    const leftHip = angles.leftHip ?? angles.left_hip;
    const rightHip = angles.rightHip ?? angles.right_hip;

    if (exercise?.toLowerCase().includes('squat')) {
      if (leftKnee !== undefined && leftKnee < 70) notes.push('Left knee angle is shallow; aim for a deeper but controlled squat depth.');
      if (rightKnee !== undefined && rightKnee < 70) notes.push('Right knee angle is shallow; aim for a deeper but controlled squat depth.');
      if (leftHip !== undefined && leftHip > 150) notes.push('Left hip angle suggests you may be staying too upright or not sitting back enough.');
      if (rightHip !== undefined && rightHip > 150) notes.push('Right hip angle suggests you may be staying too upright or not sitting back enough.');
    }

    if (issueText.includes('knee')) {
      notes.push('Knee alignment was flagged; keep knees tracking over the toes.');
    }

    if (issueText.includes('hip')) {
      notes.push('Hip position was flagged; keep hips level and controlled.');
    }

    if (issueText.includes('back')) {
      notes.push('Back position was flagged; maintain a neutral spine and brace the core.');
    }

    return notes.slice(0, 3);
  };

  const improvementPlan = getImprovementPlan();
  const angleNotes = getAngleNotes();
  const issueText = issueList.map(issue => issue.message || '').join(' ');

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

      {/* Score and Session Summary */}
      {formScore !== undefined && (
        <div className="mb-4 p-4 rounded-lg bg-blue-50 border border-blue-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Form Score</span>
            <span className="text-2xl font-bold text-blue-700">{Math.round(Number(formScore))}%</span>
          </div>
          <p className="text-sm font-semibold text-gray-900">{getScoreStatus(formScore)}</p>
          <p className="text-sm text-gray-600 mt-2">
            You completed {rep_count || 0} rep{rep_count === 1 ? '' : 's'} and the system detected the movement state as <strong>{state}</strong>.
            Focus on keeping the same controlled range and posture for every rep.
          </p>
        </div>
      )}

      {(ai_guidance || guidance || summary) && (
        <div className="mb-4 p-4 rounded-lg bg-purple-50 border border-purple-100">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Detailed Coaching Summary</h4>
          <div className="text-sm text-gray-700 whitespace-pre-line">
            {ai_guidance || guidance || summary}
          </div>
        </div>
      )}

      <div className="mb-4 p-4 rounded-lg bg-green-50 border border-green-100">
        <h4 className="text-sm font-medium text-gray-700 mb-2">How the Exercise Went</h4>
        <p className="text-sm text-gray-700">
          The movement was tracked with joint-angle data, rep count, and form issue detection.
          {issueList.length > 0
            ? ` ${issueList.length} form issue${issueList.length === 1 ? '' : 's'} were detected, so the next set should prioritize the fixes below.`
            : ' No major form issues were recorded in the latest frame, so maintain the same controlled technique.'}
        </p>
        {angleNotes.length > 0 && (
          <ul className="mt-2 space-y-1 text-sm text-gray-700">
            {angleNotes.map((note, idx) => (
              <li key={idx}>• {note}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="mb-4 p-4 rounded-lg bg-yellow-50 border border-yellow-100">
        <h4 className="text-sm font-medium text-gray-700 mb-2">How to Improve Your Form</h4>
        <ul className="space-y-2 text-sm text-gray-700">
          {improvementPlan.map((item, idx) => (
            <li key={idx}>• {item}</li>
          ))}
        </ul>
      </div>
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
