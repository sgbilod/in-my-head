export default function Collections() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Collections</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Organize your documents into collections
          </p>
        </div>
        <button className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg font-medium transition-colors">
          New Collection
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">My Documents</h3>
          <p className="text-gray-500 dark:text-gray-400 text-sm mb-4">Default collection</p>
          <p className="text-3xl font-bold text-primary-600 dark:text-primary-400">
            0 <span className="text-sm font-normal text-gray-500">documents</span>
          </p>
        </div>
      </div>
    </div>
  );
}
