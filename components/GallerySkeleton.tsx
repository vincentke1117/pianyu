import React from 'react';
import Banner from './Banner';

/**
 * Gallery 骨架屏组件
 * 在数据加载时显示，提供更好的用户体验
 */
const GallerySkeleton: React.FC = () => {
  return (
    <div className="pt-16 min-h-screen">
      {/* Banner */}
      <Banner />

      {/* Grid Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 pb-20">
        {/* Category Filter Buttons Skeleton */}
        <div className="mb-8 flex items-center gap-3 flex-wrap">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="h-10 w-24 bg-gray-200 dark:bg-mineral-800 rounded-sm animate-pulse"
            />
          ))}
        </div>

        {/* Author Filter Skeleton */}
        <div className="mb-8">
          <div className="h-10 w-full md:w-48 bg-gray-200 dark:bg-mineral-800 rounded-sm animate-pulse" />
        </div>

        {/* Section Title Skeleton */}
        <div className="mb-8 flex items-end justify-between border-b dark:border-white/5 border-black/5 pb-2">
          <div className="h-5 w-48 bg-gray-200 dark:bg-mineral-800 rounded animate-pulse" />
          <div className="h-4 w-16 bg-gray-200 dark:bg-mineral-800 rounded animate-pulse" />
        </div>

        {/* Article Cards Skeleton */}
        <div className="columns-1 md:columns-2 lg:columns-3 gap-6 space-y-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="break-inside-avoid">
              {/* Card Container */}
              <div className="rounded-sm bg-gray-100 dark:bg-mineral-800 overflow-hidden">
                {/* Image Skeleton */}
                <div className="aspect-video bg-gray-200 dark:bg-mineral-700 animate-pulse" />

                {/* Content Skeleton */}
                <div className="p-6 space-y-3">
                  {/* Metadata */}
                  <div className="flex items-center gap-4">
                    <div className="h-3 w-20 bg-gray-200 dark:bg-mineral-700 rounded animate-pulse" />
                    <div className="h-3 w-24 bg-gray-200 dark:bg-mineral-700 rounded animate-pulse" />
                  </div>

                  {/* Title */}
                  <div className="h-6 bg-gray-200 dark:bg-mineral-700 rounded animate-pulse w-3/4" />

                  {/* Quote Preview */}
                  <div className="space-y-2 pl-4 border-l-2 dark:border-white/10 border-black/10">
                    <div className="h-3 bg-gray-200 dark:bg-mineral-700 rounded animate-pulse" />
                    <div className="h-3 bg-gray-200 dark:bg-mineral-700 rounded animate-pulse w-5/6" />
                  </div>

                  {/* Tags */}
                  <div className="flex gap-2 pt-2">
                    <div className="h-6 w-12 bg-gray-200 dark:bg-mineral-700 rounded-sm animate-pulse" />
                    <div className="h-6 w-16 bg-gray-200 dark:bg-mineral-700 rounded-sm animate-pulse" />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default GallerySkeleton;
