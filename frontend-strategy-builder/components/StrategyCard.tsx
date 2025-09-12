import React, { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  Target, 
  BarChart3, 
  Zap, 
  Shield, 
  Activity,
  Settings,
  Info,
  Edit3
} from 'lucide-react';

interface StrategyCardProps {
  strategy: {
    id: string;
    name: string;
    description: string;
    category: string;
    icon: string;
    color: string;
  };
  isDragging?: boolean;
  isInPipeline?: boolean;
  config?: {
    marketCapLimit: number;
    outputCount: number;
    industry?: string;
    sector?: string;
  };
  onConfigure?: () => void;
  // Inline editing support
  isFirstStrategy?: boolean;
  previousOutputCount?: number;
  onSaveInline?: (config: { marketCapLimit: number; outputCount: number; industry?: string; sector?: string }) => void;
}

const iconMap: Record<string, React.ComponentType<any>> = {
  'trending-up': TrendingUp,
  'target': Target,
  'bar-chart': BarChart3,
  'zap': Zap,
  'shield': Shield,
  'activity': Activity,
};

const colorMap: Record<string, string> = {
  'blue': 'bg-blue-500',
  'green': 'bg-green-500',
  'purple': 'bg-purple-500',
  'orange': 'bg-orange-500',
  'red': 'bg-red-500',
  'indigo': 'bg-indigo-500',
  'pink': 'bg-pink-500',
  'teal': 'bg-teal-500',
};

const StrategyCard: React.FC<StrategyCardProps> = ({
  strategy,
  isDragging = false,
  isInPipeline = false,
  config,
  onConfigure,
  isFirstStrategy = false,
  previousOutputCount = 0,
  onSaveInline
}) => {
  const IconComponent = iconMap[strategy.icon] || TrendingUp;
  const bgColor = colorMap[strategy.color] || 'bg-blue-500';

  const [isEditing, setIsEditing] = useState(false);
  const [draftInput, setDraftInput] = useState<number>(config?.marketCapLimit ?? 1000);
  const [draftOutput, setDraftOutput] = useState<number>(config?.outputCount ?? 20);

  const effectiveInputMax = useMemo(() => (isFirstStrategy ? 1000 : Math.max(1, previousOutputCount)), [isFirstStrategy, previousOutputCount]);
  const effectiveInputMin = isFirstStrategy ? 10 : Math.max(1, previousOutputCount);
  const effectiveOutputMax = useMemo(() => Math.max(1, Math.floor((isFirstStrategy ? draftInput : previousOutputCount) * 0.8)), [isFirstStrategy, draftInput, previousOutputCount]);

  const openEditor = () => {
    setDraftInput(config?.marketCapLimit ?? 1000);
    setDraftOutput(config?.outputCount ?? 20);
    setIsEditing(true);
  };

  const saveEditor = () => {
    if (!onSaveInline) {
      setIsEditing(false);
      return;
    }
    const inputToSave = isFirstStrategy ? draftInput : previousOutputCount;
    const outputToSave = Math.min(draftOutput, Math.floor(inputToSave * 0.8) || 1);
    onSaveInline({
      marketCapLimit: inputToSave,
      outputCount: outputToSave,
      industry: config?.industry,
      sector: config?.sector,
    });
    setIsEditing(false);
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ 
        opacity: isDragging ? 0.7 : 1, 
        scale: isDragging ? 1.05 : 1,
        rotate: isDragging ? 5 : 0
      }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`
        strategy-card group relative overflow-hidden
        ${isInPipeline ? 'ring-2 ring-primary-500' : ''}
        ${isDragging ? 'dragging' : ''}
      `}
    >
      {/* Background gradient (non-interactive) */}
      <div className={`absolute inset-0 bg-gradient-to-br ${bgColor} opacity-5 pointer-events-none`} />
      
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${bgColor} text-white`}>
            <IconComponent size={20} />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{strategy.name}</h3>
            <p className="text-xs text-gray-500 capitalize">{strategy.category}</p>
          </div>
        </div>
        
        {/* Configure button for pipeline strategies */}
        {isInPipeline && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              if (onSaveInline) {
                openEditor();
              } else if (onConfigure) {
                onConfigure();
              }
            }}
            className="p-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors shadow-md z-10 relative"
            title="Edit Input/Output Counts"
          >
            <Edit3 size={18} className="text-white" />
          </button>
        )}
      </div>

      {/* Description */}
      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
        {strategy.description}
      </p>

      {/* Configuration display */}
      {isInPipeline && config && (
        <div className="space-y-2 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-600">Input Stocks:</span>
            <span className="font-medium">{config.marketCapLimit.toLocaleString()}</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-600">Output Count:</span>
            <span className="font-medium">{config.outputCount}</span>
          </div>
          {config.industry && (
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-600">Industry:</span>
              <span className="font-medium truncate ml-2">{config.industry}</span>
            </div>
          )}
          {config.sector && (
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-600">Sector:</span>
              <span className="font-medium truncate ml-2">{config.sector}</span>
            </div>
          )}
        </div>
      )}

      {/* Inline editor */}
      {isInPipeline && isEditing && (
        <div className="mt-3 space-y-4 p-3 bg-white rounded-lg border">
          <div>
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-gray-600">Input Stocks</span>
              <span className="font-medium text-blue-600">{(isFirstStrategy ? draftInput : previousOutputCount).toLocaleString()}</span>
            </div>
            <input
              type="range"
              min={effectiveInputMin}
              max={effectiveInputMax}
              step={isFirstStrategy ? 10 : 1}
              disabled={!isFirstStrategy}
              value={isFirstStrategy ? draftInput : previousOutputCount}
              onChange={(e) => setDraftInput(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
            />
            {!isFirstStrategy && (
              <p className="text-[11px] text-gray-500 mt-1">Input comes from previous strategy's output</p>
            )}
          </div>

          <div>
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-gray-600">Output Stocks</span>
              <span className="font-medium text-green-600">{Math.min(draftOutput, effectiveOutputMax)}</span>
            </div>
            <input
              type="range"
              min={1}
              max={effectiveOutputMax}
              step={1}
              value={Math.min(draftOutput, effectiveOutputMax)}
              onChange={(e) => setDraftOutput(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
            />
          </div>

          <div className="flex justify-end gap-2">
            <button
              onClick={() => setIsEditing(false)}
              className="px-3 py-1.5 text-sm rounded-md bg-gray-100 hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              onClick={saveEditor}
              className="px-3 py-1.5 text-sm rounded-md bg-blue-600 text-white hover:bg-blue-700"
            >
              Save
            </button>
          </div>
        </div>
      )}

      {/* Drag indicator */}
      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <div className="w-2 h-2 bg-gray-400 rounded-full" />
        <div className="w-2 h-2 bg-gray-400 rounded-full mt-1" />
        <div className="w-2 h-2 bg-gray-400 rounded-full mt-1" />
      </div>

      {/* Hover effect (non-interactive) */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-0 group-hover:opacity-10 transition-opacity pointer-events-none" />
    </motion.div>
  );
};

export default StrategyCard;
