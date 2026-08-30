import NavBar from './NavBar'

export default function Layout({ children }) {
  return (
    <div>
      <NavBar />
      <main style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
        {children}
      </main>
    </div>
  )
}