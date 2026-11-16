import Card, { SectionHeader } from '../../components/ui/Card'
import Notice from '../../components/ui/Notice'
import Skeleton from '../../components/ui/Skeleton'

// One admin table in one card: title and count, the toolbar, then exactly one of loading, error (with Retry)
// or the table (which shows its own empty message). The table runs edge to edge (DataTable flush).
//   query     the react-query result the table shows: { isLoading, isError, isFetching, refetch }
//   errorText what to say when it fails to load
export default function TableCard({ id, title, description, aside, toolbar, notices, query, errorText, footer, children }) {
  const ready = !query.isLoading && !query.isError
  return (
    <Card flush aria-labelledby={id}>
      <div className="flex flex-col gap-4 p-4 sm:p-6">
        <SectionHeader id={id} title={title} description={description} aside={ready ? aside : null} className="!mb-0" />
        {toolbar}
        {notices}
      </div>
      {query.isLoading ? (
        <div className="px-4 pb-4 sm:px-6 sm:pb-6"><Skeleton label={`Loading ${title.toLowerCase()}`} className="h-32" /></div>
      ) : query.isError ? (
        <div className="px-4 pb-4 sm:px-6 sm:pb-6">
          <Notice tone="critical" onRetry={() => query.refetch()} retrying={query.isFetching}>
            <p>{errorText}</p>
          </Notice>
        </div>
      ) : (
        children
      )}
      {footer && ready && <p className="m-0 border-t border-border px-4 py-3 text-small text-ink-secondary sm:px-6">{footer}</p>}
    </Card>
  )
}
