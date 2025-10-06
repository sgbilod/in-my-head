export default function Search() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Search</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Search across all your documents
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="max-w-2xl mx-auto">
          <input
            type="text"
            placeholder="Search for anything..."
            className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white text-lg"
          />
          <p className="text-gray-500 dark:text-gray-400 mt-4 text-center">
            Enter keywords to search through your documents
          </p>
        </div>
      </div>
    </div>
  )
}
