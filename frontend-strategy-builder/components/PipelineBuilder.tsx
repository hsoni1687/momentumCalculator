import React, { useState } from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from 'react-beautiful-dnd';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Save, ArrowRight, Settings, GripVertical } from 'lucide-react';
import StrategyCard from './StrategyCard';
import StrategyConfigModal from './StrategyConfigModal';
import { Strategy, StrategyConfig } from '@/services/api';

interface PipelineBuilderProps {
  availableStrategies: Strategy[];
  pipeline: StrategyConfig[];
  onPipelineChange: (pipeline: StrategyConfig[]) => void;
  onSave: () => void;
  pipelineResults: any[];
  isExecuting: boolean;
}

const PipelineBuilder: React.FC<PipelineBuilderProps> = ({
  availableStrategies,
  pipeline,
  onPipelineChange,
  onSave,
  pipelineResults,
  isExecuting
}) => {
  const [configModalOpen, setConfigModalOpen] = useState(false);
  const [configStrategyIndex, setConfigStrategyIndex] = useState<number | null>(null);

  const handleDragEnd = (result: DropResult) => {
    const { destination, source, draggableId } = result;

    if (!destination) return;

    // If dropped in the same position
    if (destination.droppableId === source.droppableId && destination.index === source.index) {
      return;
    }

    // If dropped from available strategies to pipeline
    if (source.droppableId === 'available-strategies' && destination.droppableId === 'pipeline') {
      const strategy = availableStrategies.find(s => s.id === draggableId);
      if (strategy) {
        const newPipeline = Array.from(pipeline);

        // Determine input for the new strategy based on previous tile's output
        const previousOutput = destination.index > 0
          ? (newPipeline[destination.index - 1]?.outputCount || 1000)
          : 1000;

        const defaultOutput = Math.min(20, Math.floor(previousOutput * 0.8) || 1);

        const newConfig: StrategyConfig = {
          strategyId: strategy.id,
          marketCapLimit: previousOutput,
          outputCount: defaultOutput,
        };

        // Insert at the drop position
        newPipeline.splice(destination.index, 0, newConfig);

        // Propagate inputs downstream from the inserted index
        for (let i = destination.index + 1; i < newPipeline.length; i++) {
          const prevOut = newPipeline[i - 1].outputCount;
          newPipeline[i] = {
            ...newPipeline[i],
            marketCapLimit: prevOut,
            outputCount: Math.min(newPipeline[i].outputCount, Math.floor(prevOut * 0.8) || 1),
          };
        }

        onPipelineChange(newPipeline);
      }
    }
    
    // If reordering within pipeline
    else if (source.droppableId === 'pipeline' && destination.droppableId === 'pipeline') {
      const newPipeline = Array.from(pipeline);
      const [removed] = newPipeline.splice(source.index, 1);
      newPipeline.splice(destination.index, 0, removed);
      
      // Auto-adjust input/output counts based on new positions
      const adjustedPipeline = newPipeline.map((config, index) => {
        if (index === 0) {
          // First strategy: ensure it has market cap limit for input
          return {
            ...config,
            marketCapLimit: config.marketCapLimit || 1000,
            outputCount: Math.min(config.outputCount, Math.floor((config.marketCapLimit || 1000) * 0.8))
          };
        } else {
          // Subsequent strategies: input comes from previous strategy's output
          const previousOutput = newPipeline[index - 1]?.outputCount || 20;
          return {
            ...config,
            marketCapLimit: previousOutput, // Input count = previous output
            outputCount: Math.min(config.outputCount, Math.floor(previousOutput * 0.8) || 1)
          };
        }
      });
      
      onPipelineChange(adjustedPipeline);
    }
  };

  const removeStrategy = (index: number) => {
    const newPipeline = pipeline.filter((_, i) => i !== index);
    onPipelineChange(newPipeline);
  };

  const getStrategyById = (id: string) => {
    return availableStrategies.find(s => s.id === id);
  };

  const handleConfigureStrategy = (index: number) => {
    console.log('handleConfigureStrategy called for index:', index);
    console.log('Strategy config:', pipeline[index]);
    setConfigStrategyIndex(index);
    setConfigModalOpen(true);
    console.log('Modal should be open now');
  };

  const handleSaveConfig = (newConfig: StrategyConfig) => {
    if (configStrategyIndex !== null) {
      const newPipeline = [...pipeline];
      newPipeline[configStrategyIndex] = newConfig;
      onPipelineChange(newPipeline);
    }
  };

  const getCurrentStrategy = () => {
    if (configStrategyIndex !== null && pipeline[configStrategyIndex]) {
      const config = pipeline[configStrategyIndex];
      return availableStrategies.find(s => s.id === config.strategyId) || null;
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Pipeline Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Strategy Pipeline</h2>
          <p className="text-gray-600">Drag strategies to build your custom pipeline - results update automatically</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={onSave}
            className="btn-secondary flex items-center space-x-2"
            disabled={pipeline.length === 0}
          >
            <Save size={16} />
            <span>Save Pipeline</span>
          </button>
        </div>
      </div>

      <DragDropContext onDragEnd={handleDragEnd}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Available Strategies */}
          <div className="lg:col-span-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Strategies</h3>
            <Droppable droppableId="available-strategies">
              {(provided, snapshot) => (
                <div
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  className={`
                    drop-zone min-h-[400px] p-4
                    ${snapshot.isDraggingOver ? 'drop-zone-active' : ''}
                  `}
                >
                  <AnimatePresence>
                    {availableStrategies
                      .filter(strategy => !pipeline.some(config => config.strategyId === strategy.id))
                      .map((strategy, index) => (
                      <Draggable key={strategy.id} draggableId={strategy.id} index={index}>
                        {(provided, snapshot) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            {...provided.dragHandleProps}
                            className="mb-3"
                          >
                            <StrategyCard
                              strategy={strategy}
                              isDragging={snapshot.isDragging}
                            />
                          </div>
                        )}
                      </Draggable>
                    ))}
                  </AnimatePresence>
                  {provided.placeholder}
                  
                  {availableStrategies.length === 0 && (
                    <div className="text-center text-gray-500 py-8">
                      <Settings size={48} className="mx-auto mb-4 opacity-50" />
                      <p>No strategies available</p>
                    </div>
                  )}
                </div>
              )}
            </Droppable>
          </div>

          {/* Pipeline */}
          <div className="lg:col-span-2">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Your Pipeline ({pipeline.length} strategies)
            </h3>
            <Droppable droppableId="pipeline">
              {(provided, snapshot) => (
                <div
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  className={`
                    drop-zone min-h-[400px] p-4
                    ${snapshot.isDraggingOver ? 'drop-zone-active' : ''}
                    ${pipeline.length === 0 ? 'flex items-center justify-center' : ''}
                  `}
                >
                  <AnimatePresence>
                    {pipeline.map((config, index) => {
                      const strategy = getStrategyById(config.strategyId);
                      if (!strategy) return null;

                      return (
                        <Draggable key={`${config.strategyId}-${index}`} draggableId={`${config.strategyId}-${index}`} index={index}>
                          {(provided, snapshot) => (
                            <div className="mb-4">
                              {/* Draggable wrapper (moves whole tile) */}
                              <div
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                className="relative flex items-start gap-3"
                              >
                                {/* Drag Handle - only this captures drag gestures */}
                                <div
                                  {...provided.dragHandleProps}
                                  className="flex items-center justify-center w-10 h-16 bg-gray-300 hover:bg-gray-400 rounded-lg cursor-grab active:cursor-grabbing transition-colors shadow-sm mt-2"
                                  title="Drag to reorder strategies"
                                >
                                  <GripVertical size={18} className="text-gray-600" />
                                </div>

                                {/* Strategy Card (not draggable, fully interactive) */}
                                <div className="flex-1">
                                  <StrategyCard
                                    strategy={strategy}
                                    isDragging={snapshot.isDragging}
                                    isInPipeline={true}
                                    config={config}
                                    isFirstStrategy={index === 0}
                                    previousOutputCount={index > 0 ? (pipeline[index - 1]?.outputCount || 0) : 0}
                                    onSaveInline={(newPartial) => {
                                      const updated = [...pipeline];
                                      const inputForCurrent = index === 0 ? newPartial.marketCapLimit : (updated[index - 1]?.outputCount || 0);
                                      updated[index] = {
                                        ...updated[index],
                                        marketCapLimit: inputForCurrent,
                                        outputCount: Math.min(newPartial.outputCount, Math.floor(inputForCurrent * 0.8) || 1),
                                      };
                                      // Propagate inputs downstream
                                      for (let i = index + 1; i < updated.length; i++) {
                                        const prevOut = updated[i - 1].outputCount;
                                        updated[i] = {
                                          ...updated[i],
                                          marketCapLimit: prevOut,
                                          outputCount: Math.min(updated[i].outputCount, Math.floor(prevOut * 0.8) || 1),
                                        };
                                      }
                                      onPipelineChange(updated);
                                    }}
                                    onConfigure={() => handleConfigureStrategy(index)}
                                  />
                                </div>
                              </div>

                              {/* Arrow to next strategy */}
                              {index < pipeline.length - 1 && (
                                <div className="flex justify-center mt-2">
                                  <ArrowRight size={20} className="text-gray-400" />
                                </div>
                              )}
                            </div>
                          )}
                        </Draggable>
                      );
                    })}
                  </AnimatePresence>
                  {provided.placeholder}
                  
                  {pipeline.length === 0 && (
                    <div className="text-center text-gray-500 py-8">
                      <Plus size={48} className="mx-auto mb-4 opacity-50" />
                      <p className="text-lg font-medium mb-2">Build Your Pipeline</p>
                      <p>Drag strategies from the left to start building your custom pipeline</p>
                    </div>
                  )}
                </div>
              )}
            </Droppable>
          </div>
        </div>
      </DragDropContext>

      {/* Real-time Results Section */}
      {pipeline.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Pipeline Results {isExecuting && <span className="text-sm text-blue-600">(Executing...)</span>}
          </h3>
          
          {pipelineResults.length > 0 ? (
            <div className="space-y-4">
              {pipelineResults.map((result, index) => (
                <div key={index} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-gray-900">{result.strategyName}</h4>
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <span>{result.inputCount} → {result.outputCount} stocks</span>
                      <span>{result.executionTime}ms</span>
                    </div>
                  </div>
                  
                  {result.stocks && result.stocks.length > 0 && (
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
                      {result.stocks.slice(0, 12).map((stock: any, stockIndex: number) => (
                        <div key={stockIndex} className="p-2 bg-white rounded border text-xs">
                          <div className="font-medium">{stock.stock}</div>
                          <div className="text-gray-600">Score: {stock.score?.toFixed(3) || 'N/A'}</div>
                        </div>
                      ))}
                      {result.stocks.length > 12 && (
                        <div className="p-2 bg-blue-50 rounded border text-xs text-blue-600 font-medium">
                          +{result.stocks.length - 12} more
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : isExecuting ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Executing pipeline...</p>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>Add strategies to see results</p>
            </div>
          )}
        </div>
      )}

      {/* Configuration Modal */}
      <StrategyConfigModal
        isOpen={configModalOpen}
        onClose={() => {
          setConfigModalOpen(false);
          setConfigStrategyIndex(null);
        }}
        onSave={handleSaveConfig}
        strategy={getCurrentStrategy()}
        currentConfig={configStrategyIndex !== null ? pipeline[configStrategyIndex] : undefined}
        isFirstStrategy={configStrategyIndex === 0}
        previousOutputCount={configStrategyIndex !== null && configStrategyIndex > 0 ? pipeline[configStrategyIndex - 1]?.outputCount || 20 : 0}
      />

    </div>
  );
};

export default PipelineBuilder;
