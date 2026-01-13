import { useState, useEffect } from 'react';

/**
 * 防抖值 Hook
 * 延迟更新值，减少频繁计算
 *
 * @param value - 需要防抖的值
 * @param delay - 延迟时间（毫秒），默认 300ms
 * @returns 防抖后的值
 *
 * @example
 * const [query, setQuery] = useState('');
 * const debouncedQuery = useDebouncedValue(query, 300);
 * // debouncedQuery 会在 query 停止变化 300ms 后更新
 */
export const useDebouncedValue = <T,>(value: T, delay: number = 300): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // 设置定时器，延迟更新值
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // 清理函数：如果 value 或 delay 变化，取消之前的定时器
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};
