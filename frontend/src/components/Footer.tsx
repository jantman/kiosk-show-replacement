import React, { useState, useEffect } from 'react';

const Footer: React.FC = () => {
  const [version, setVersion] = useState<string>('');

  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const response = await fetch('/api/v1/version');
        if (response.ok) {
          const data = await response.json();
          if (data?.data?.version) {
            setVersion(data.data.version);
          }
        }
      } catch {
        // Silently fail - footer will just omit version
      }
    };
    fetchVersion();
  }, []);

  return (
    <footer className="bg-light mt-5 py-4">
      <div className="container text-center">
        <p className="text-muted mb-0">
          <a
            href="https://github.com/jantman/kiosk-show-replacement"
            target="_blank"
            rel="noopener noreferrer"
          >
            kiosk-show-replacement{version ? ` v${version}` : ''}
          </a>{' '}
          is{' '}
          <a
            href="https://opensource.org/license/mit"
            target="_blank"
            rel="noopener noreferrer"
          >
            Free and Open Source Software
          </a>
          , Copyright 2026 Jason Antman.
        </p>
      </div>
    </footer>
  );
};

export default Footer;
