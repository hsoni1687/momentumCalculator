import React from 'react';
import Head from 'next/head';
import { TrendingUp, Database, Server } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, title = 'Momentum Calculator' }) => {
  return (
    <>
      <Head>
        <title>{title}</title>
        <meta name="description" content="Modern momentum analysis for Indian stocks" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center space-x-3">
                <TrendingUp className="h-8 w-8 text-primary-600" />
                <div>
                  <h1 className="text-xl font-bold text-gray-900">Momentum Calculator</h1>
                  <p className="text-sm text-gray-500">Indian Stock Analysis</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <Database className="h-4 w-4" />
                  <span>PostgreSQL</span>
                </div>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <Server className="h-4 w-4" />
                  <span>FastAPI</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>

        {/* Footer */}
        <footer className="bg-white border-t border-gray-200 mt-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="text-center text-sm text-gray-500">
              <p>© 2024 Momentum Calculator. Built with React, Next.js, and FastAPI.</p>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
};

export default Layout;
