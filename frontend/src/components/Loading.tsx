import React from 'react';

export const Loading: React.FC = () => (
  <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
    <div className="text-center">
      <div className="inline-block animate-spin rounded-full border-4 border-gray-300 border-t-blue-600 h-12 w-12 mb-4"></div>
      <p className="text-gray-600 dark:text-gray-400">Loading...</p>
    </div>
  </div>
);

export default Loading;