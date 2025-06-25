import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
}

const Card: React.FC<CardProps> = ({
  children,
  className = '',
  padding = 'md',
  hover = false
}) => {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8'
  };

  const hoverClass = hover ? 'hover:shadow-lg hover:-translate-y-1' : '';

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 transition-all duration-200 ${paddingClasses[padding]} ${hoverClass} ${className}`}>
      {children}
    </div>
  );
};

export default Card;