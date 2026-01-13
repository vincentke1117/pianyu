import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Feather } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

/**
 * 错误边界组件
 * 捕获子组件树中的 JavaScript 错误，防止整个应用崩溃
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // 可以将错误发送到错误监控服务
    // logErrorToService(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-paper-50 dark:bg-mineral-900">
          <div className="text-center px-6">
            <div className="mb-8">
              <Feather className="w-16 h-16 mx-auto text-gold-light dark:text-gold opacity-50" />
            </div>
            <h1 className="text-2xl font-serif font-bold mb-4 dark:text-mineral-100 text-paper-900">
              羽毛飞走了...
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mb-8 max-w-md">
              我们遇到了一些问题，但别担心，您的珍藏依然安全。
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => window.location.reload()}
                className="px-6 py-3 rounded-sm bg-gold text-white font-medium hover:opacity-90 transition-opacity"
              >
                重新加载
              </button>
              <button
                onClick={() => this.setState({ hasError: false })}
                className="px-6 py-3 rounded-sm border dark:border-white/10 border-black/5 dark:text-gray-300 text-gray-600 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors"
              >
                返回首页
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
