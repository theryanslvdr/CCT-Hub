import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  handleReload = () => {
    // Clear any potentially corrupted state
    try {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    } catch (e) { /* ignore */ }
    window.location.href = '/login';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#0a0a0a',
          padding: '24px',
        }}>
          <div style={{
            maxWidth: '400px',
            width: '100%',
            background: '#111111',
            border: '1px solid #222222',
            borderRadius: '16px',
            padding: '32px',
            textAlign: 'center',
          }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #f97316, #ea580c)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px',
              fontSize: '24px',
            }}>
              !
            </div>
            <h2 style={{ color: '#fff', fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
              Something went wrong
            </h2>
            <p style={{ color: '#a1a1aa', fontSize: '14px', marginBottom: '24px', lineHeight: '1.5' }}>
              An unexpected error occurred. Click below to reload the app.
            </p>
            <button
              onClick={this.handleReload}
              data-testid="error-boundary-reload"
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '10px',
                background: '#f97316',
                color: '#fff',
                border: 'none',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              Reload App
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
