"use client";

import { useState, useMemo, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ParameterRange, OptimizationConfig, STRATEGY_TEMPLATES } from "@/types/optimization";
import { Trash2, Plus, Settings, Sparkles, ChevronDown, ChevronRight } from "lucide-react";
import {
  extractParametersFromRules,
  suggestOptimizationRange,
  convertToParameterRanges,
  type ExtractedParameter,
} from "@/lib/parameterExtractor";

interface ParameterConfigProps {
  config: OptimizationConfig;
  onConfigChange: (config: OptimizationConfig) => void;
  selectedTemplate?: string;
  onTemplateChange?: (templateId: string) => void;
  currentRules?: {
    openRule?: string;
    closeRule?: string;
    buyRule?: string;
    sellRule?: string;
  };
}

export function ParameterConfig({
  config,
  onConfigChange,
  selectedTemplate,
  onTemplateChange,
  currentRules,
}: ParameterConfigProps) {
  const [isAddingParameter, setIsAddingParameter] = useState(false);
  const [extractedParams, setExtractedParams] = useState<ExtractedParameter[]>([]);
  const [showDetectedParams, setShowDetectedParams] = useState(true);

  // Auto-extract parameters when rules change
  useEffect(() => {
    if (!currentRules) {
      setExtractedParams([]);
      return;
    }

    const rules: Record<string, string> = {};
    if (currentRules.openRule) rules["open_rule"] = currentRules.openRule;
    if (currentRules.closeRule) rules["close_rule"] = currentRules.closeRule;
    if (currentRules.buyRule) rules["buy_rule"] = currentRules.buyRule;
    if (currentRules.sellRule) rules["sell_rule"] = currentRules.sellRule;

    const extracted = extractParametersFromRules(rules);
    setExtractedParams(extracted);
  }, [currentRules]);

  // Get unique parameters that haven't been added yet
  const newParams = useMemo(() => {
    const existingKeys = new Set(
      config.parameter_ranges.map((r) => `${r.indicator}_${r.parameter_name}`)
    );
    return extractedParams.filter(
      (p) => !existingKeys.has(`${p.indicator}_${p.parameterName}`)
    );
  }, [extractedParams, config.parameter_ranges]);

  // Add all detected parameters
  const handleAddAllDetected = () => {
    const newRanges = convertToParameterRanges(newParams);
    onConfigChange({
      ...config,
      parameter_ranges: [...config.parameter_ranges, ...newRanges],
    });
  };

  // Add a single detected parameter
  const handleAddDetectedParam = (param: ExtractedParameter) => {
    const range = suggestOptimizationRange(param);
    const newRange: ParameterRange = {
      indicator: param.indicator,
      parameter_name: `${param.indicator}_${param.parameterName}`,
      type: range.type,
      ...(range.type === "range"
        ? { min: range.min, max: range.max, step: range.step }
        : { values: range.values }),
    };

    onConfigChange({
      ...config,
      parameter_ranges: [...config.parameter_ranges, newRange],
    });
  };

  // Check if rules have content
  const hasRules = useMemo(() => {
    if (!currentRules) return false;
    return !!(
      currentRules.openRule ||
      currentRules.closeRule ||
      currentRules.buyRule ||
      currentRules.sellRule
    );
  }, [currentRules]);

  // Add a new parameter range
  const addParameterRange = (range: ParameterRange) => {
    const newConfig = {
      ...config,
      parameter_ranges: [...config.parameter_ranges, range],
    };
    onConfigChange(newConfig);
    setIsAddingParameter(false);
  };

  // Remove a parameter range
  const removeParameterRange = (index: number) => {
    const newConfig = {
      ...config,
      parameter_ranges: config.parameter_ranges.filter((_, i) => i !== index),
    };
    onConfigChange(newConfig);
  };

  // Update a parameter range
  const updateParameterRange = (index: number, range: ParameterRange) => {
    const newRanges = [...config.parameter_ranges];
    newRanges[index] = range;
    onConfigChange({ ...config, parameter_ranges: newRanges });
  };

  return (
    <div className="space-y-4">
      {/* Strategy Template Selection */}
      {onTemplateChange && (
        <Card className="p-4 bg-slate-900/50 border-slate-800">
          <div className="flex items-center gap-2 mb-3">
            <Settings className="w-4 h-4 text-sky-400" />
            <h3 className="text-sm font-semibold text-slate-300">策略模板</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            {Object.entries(STRATEGY_TEMPLATES).map(([id, template]) => (
              <button
                key={id}
                onClick={() => onTemplateChange(id)}
                className={`p-3 rounded-lg border text-left transition-all ${
                  selectedTemplate === id
                    ? "bg-sky-600/20 border-sky-500 text-sky-300"
                    : "bg-slate-800/50 border-slate-700 text-slate-400 hover:border-slate-600"
                }`}
              >
                <div className="font-medium text-sm">{template.name}</div>
                <div className="text-xs opacity-70 mt-1">{template.description}</div>
              </button>
            ))}
          </div>
        </Card>
      )}

      {/* Auto-detected Parameters Notice */}
      {hasRules && extractedParams.length > 0 && (
        <Card className={`p-4 bg-gradient-to-r from-emerald-900/20 to-sky-900/20 border-emerald-700/50 transition-all`}>
          <button
            onClick={() => setShowDetectedParams(!showDetectedParams)}
            className="w-full flex items-center justify-between"
          >
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-emerald-400" />
              <div className="text-left">
                <h4 className="text-sm font-semibold text-emerald-300">
                  检测到 {extractedParams.length} 个可优化参数
                </h4>
                <p className="text-xs text-emerald-400/70">
                  从当前规则中自动识别，点击展开查看详情
                </p>
              </div>
            </div>
            {showDetectedParams ? (
              <ChevronDown className="w-5 h-5 text-emerald-400" />
            ) : (
              <ChevronRight className="w-5 h-5 text-emerald-400" />
            )}
          </button>

          {showDetectedParams && (
            <div className="mt-4 space-y-3">
              {/* Detected parameters list */}
              <div className="space-y-2">
                {extractedParams.map((param, idx) => {
                  const isNewParam = newParams.some(
                    (p) => p.indicator === param.indicator && p.parameterName === param.parameterName
                  );
                  return (
                    <div
                      key={`${param.indicator}_${param.parameterName}_${idx}`}
                      className={`flex items-center justify-between p-2 rounded-lg ${
                        isNewParam
                          ? "bg-emerald-800/30 border border-emerald-600/50"
                          : "bg-slate-800/50 border border-slate-700"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm text-sky-300">
                          {param.indicator}
                        </span>
                        <span className="text-xs text-slate-400">.</span>
                        <span className="text-sm text-slate-300">{param.parameterName}</span>
                        <span className="text-xs text-slate-500">=</span>
                        <span className="font-mono text-sm text-emerald-400">
                          {param.currentValue}
                        </span>
                        {isNewParam && (
                          <span className="text-xs px-2 py-0.5 rounded bg-emerald-600 text-white">
                            新
                          </span>
                        )}
                      </div>
                      {isNewParam && (
                        <Button
                          onClick={() => handleAddDetectedParam(param)}
                          size="sm"
                          variant="ghost"
                          className="text-emerald-400 hover:text-emerald-300 h-7 px-2"
                        >
                          添加
                        </Button>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Add all button */}
              {newParams.length > 0 && (
                <Button
                  onClick={handleAddAllDetected}
                  className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
                  size="sm"
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  全部添加 ({newParams.length} 个参数)
                </Button>
              )}
            </div>
          )}
        </Card>
      )}

      {/* Parameter Ranges List */}
      <Card className="p-4 bg-slate-900/50 border-slate-800">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-300">参数范围配置</h3>
          <Button
            onClick={() => setIsAddingParameter(true)}
            size="sm"
            variant="outline"
            className="text-sky-400 border-sky-700 hover:bg-sky-900/20"
          >
            <Plus className="w-4 h-4 mr-1" />
            手动添加参数
          </Button>
        </div>

        {config.parameter_ranges.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-sm">
            {hasRules ? (
              <div>
                <p className="mb-2">上方卡片显示了检测到的参数</p>
                <p className="text-xs">或点击"手动添加参数"自定义配置</p>
              </div>
            ) : (
              <p>请先配置交易策略规则，系统将自动识别可优化参数</p>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            {config.parameter_ranges.map((range, index) => (
              <ParameterRangeCard
                key={index}
                range={range}
                index={index}
                onUpdate={(r) => updateParameterRange(index, r)}
                onRemove={() => removeParameterRange(index)}
              />
            ))}
          </div>
        )}
      </Card>

      {/* New Parameter Form */}
      {isAddingParameter && (
        <NewParameterForm
          onAdd={addParameterRange}
          onCancel={() => setIsAddingParameter(false)}
        />
      )}

      {/* Optimization Settings */}
      <Card className="p-4 bg-slate-900/50 border-slate-800">
        <h3 className="text-sm font-semibold text-slate-300 mb-3">优化设置</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Random Samples */}
          <div>
            <label className="block text-xs text-slate-400 mb-1">
              随机采样次数
            </label>
            <input
              type="number"
              min={1}
              max={1000}
              value={config.random_samples}
              onChange={(e) =>
                onConfigChange({
                  ...config,
                  random_samples: parseInt(e.target.value) || 50,
                })
              }
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 text-sm focus:outline-none focus:border-sky-500"
            />
          </div>

          {/* Top N Candidates */}
          <div>
            <label className="block text-xs text-slate-400 mb-1">
              返回候选数量
            </label>
            <input
              type="number"
              min={1}
              max={50}
              value={config.top_n_candidates}
              onChange={(e) =>
                onConfigChange({
                  ...config,
                  top_n_candidates: parseInt(e.target.value) || 5,
                })
              }
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 text-sm focus:outline-none focus:border-sky-500"
            />
          </div>

          {/* Screening Metric */}
          <div>
            <label className="block text-xs text-slate-400 mb-1">
              优化目标
            </label>
            <select
              value={config.screening_metric}
              onChange={(e) =>
                onConfigChange({
                  ...config,
                  screening_metric: e.target.value as
                    | "sharpe_ratio"
                    | "total_return",
                })
              }
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 text-sm focus:outline-none focus:border-sky-500"
            >
              <option value="sharpe_ratio">夏普比率</option>
              <option value="total_return">总收益率</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Statistics Preview */}
      <StatsPreview config={config} />
    </div>
  );
}

// Parameter Range Card Component
interface ParameterRangeCardProps {
  range: ParameterRange;
  index: number;
  onUpdate: (range: ParameterRange) => void;
  onRemove: () => void;
}

function ParameterRangeCard({
  range,
  index,
  onUpdate,
  onRemove,
}: ParameterRangeCardProps) {
  const [isEditing, setIsEditing] = useState(false);

  if (isEditing) {
    return (
      <Card className="p-4 bg-slate-800/50 border-sky-700">
        <EditParameterForm
          range={range}
          onSave={(r) => {
            onUpdate(r);
            setIsEditing(false);
          }}
          onCancel={() => setIsEditing(false)}
        />
      </Card>
    );
  }

  return (
    <Card className="p-3 bg-slate-800/30 border-slate-700 hover:border-slate-600 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sky-400 font-mono text-sm">
              {range.indicator}.{range.parameter_name}
            </span>
            <span className="text-xs px-2 py-0.5 rounded bg-slate-700 text-slate-400">
              {range.type === "range" ? "范围" : "自定义"}
            </span>
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {range.type === "range"
              ? `${range.min} - ${range.max} (步长: ${range.step})`
              : range.values?.join(", ")}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={() => setIsEditing(true)}
            size="sm"
            variant="ghost"
            className="text-slate-400 hover:text-slate-200"
          >
            编辑
          </Button>
          <Button
            onClick={onRemove}
            size="sm"
            variant="ghost"
            className="text-red-400 hover:text-red-300"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
}

// Edit Parameter Form Component
interface EditParameterFormProps {
  range: ParameterRange;
  onSave: (range: ParameterRange) => void;
  onCancel: () => void;
}

function EditParameterForm({ range, onSave, onCancel }: EditParameterFormProps) {
  const [indicator, setIndicator] = useState(range.indicator);
  const [paramName, setParamName] = useState(range.parameter_name);
  const [type, setType] = useState<"range" | "custom">(range.type);
  const [min, setMin] = useState(range.min ?? 5);
  const [max, setMax] = useState(range.max ?? 50);
  const [step, setStep] = useState(range.step ?? 5);
  const [customValues, setCustomValues] = useState(
    range.values?.join(", ") ?? ""
  );

  const handleSave = () => {
    if (type === "range") {
      onSave({
        indicator,
        parameter_name: paramName,
        type,
        min,
        max,
        step,
      });
    } else {
      const values = customValues
        .split(",")
        .map((v) => parseInt(v.trim()))
        .filter((v) => !isNaN(v));
      onSave({
        indicator,
        parameter_name: paramName,
        type,
        values,
      });
    }
  };

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-slate-400 mb-1">指标</label>
          <select
            value={indicator}
            onChange={(e) => setIndicator(e.target.value)}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-slate-200 text-sm"
          >
            <option value="SMA">SMA</option>
            <option value="RSI">RSI</option>
            <option value="MACD">MACD</option>
            <option value="EMA">EMA</option>
            <option value="CUSTOM">自定义</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">参数名</label>
          <input
            type="text"
            value={paramName}
            onChange={(e) => setParamName(e.target.value)}
            placeholder="如: fast_window"
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-slate-200 text-sm"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs text-slate-400 mb-1">类型</label>
        <div className="flex gap-2">
          <button
            onClick={() => setType("range")}
            className={`flex-1 px-3 py-2 rounded text-sm transition-all ${
              type === "range"
                ? "bg-sky-600 text-white"
                : "bg-slate-700 text-slate-400"
            }`}
          >
            范围
          </button>
          <button
            onClick={() => setType("custom")}
            className={`flex-1 px-3 py-2 rounded text-sm transition-all ${
              type === "custom"
                ? "bg-sky-600 text-white"
                : "bg-slate-700 text-slate-400"
            }`}
          >
            自定义
          </button>
        </div>
      </div>

      {type === "range" ? (
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-slate-400 mb-1">最小值</label>
            <input
              type="number"
              value={min}
              onChange={(e) => setMin(parseInt(e.target.value) || 1)}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-slate-200 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">最大值</label>
            <input
              type="number"
              value={max}
              onChange={(e) => setMax(parseInt(e.target.value) || 100)}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-slate-200 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">步长</label>
            <input
              type="number"
              value={step}
              onChange={(e) => setStep(parseInt(e.target.value) || 1)}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-slate-200 text-sm"
            />
          </div>
        </div>
      ) : (
        <div>
          <label className="block text-xs text-slate-400 mb-1">
            值列表 (逗号分隔)
          </label>
          <input
            type="text"
            value={customValues}
            onChange={(e) => setCustomValues(e.target.value)}
            placeholder="5, 10, 15, 20, 30"
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-slate-200 text-sm"
          />
        </div>
      )}

      <div className="flex gap-2 justify-end">
        <Button onClick={onCancel} size="sm" variant="ghost">
          取消
        </Button>
        <Button onClick={handleSave} size="sm" className="bg-sky-600">
          保存
        </Button>
      </div>
    </div>
  );
}

// New Parameter Form Component
interface NewParameterFormProps {
  onAdd: (range: ParameterRange) => void;
  onCancel: () => void;
}

function NewParameterForm({ onAdd, onCancel }: NewParameterFormProps) {
  const [indicator, setIndicator] = useState("SMA");
  const [paramName, setParamName] = useState("");
  const [type, setType] = useState<"range" | "custom">("range");
  const [min, setMin] = useState(5);
  const [max, setMax] = useState(50);
  const [step, setStep] = useState(5);
  const [customValues, setCustomValues] = useState("");

  const handleAdd = () => {
    if (!paramName.trim()) return;

    if (type === "range") {
      onAdd({
        indicator,
        parameter_name: paramName,
        type,
        min,
        max,
        step,
      });
    } else {
      const values = customValues
        .split(",")
        .map((v) => parseInt(v.trim()))
        .filter((v) => !isNaN(v));
      onAdd({
        indicator,
        parameter_name: paramName,
        type,
        values,
      });
    }
  };

  return (
    <Card className="p-4 bg-slate-800/50 border-sky-600">
      <h4 className="text-sm font-semibold text-slate-300 mb-3">添加新参数</h4>
      <EditParameterForm
        range={{
          indicator,
          parameter_name: paramName,
          type,
          min,
          max,
          step,
          values: customValues
            .split(",")
            .map((v) => parseInt(v.trim()))
            .filter((v) => !isNaN(v)),
        }}
        onSave={handleAdd}
        onCancel={onCancel}
      />
    </Card>
  );
}

// Stats Preview Component
interface StatsPreviewProps {
  config: OptimizationConfig;
}

function StatsPreview({ config }: StatsPreviewProps) {
  // Calculate total combinations
  const totalCombinations = config.parameter_ranges.reduce(
    (acc, range) => {
      const count =
        range.type === "range"
          ? Math.floor((range.max! - range.min!) / range.step!) + 1
          : range.values?.length || 0;
      return acc * (count || 1);
    },
    1
  );

  return (
    <Card className="p-4 bg-slate-900/50 border-slate-800">
      <h3 className="text-sm font-semibold text-slate-300 mb-3">配置预览</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>
          <div className="text-slate-500 text-xs">参数数量</div>
          <div className="text-slate-200 font-medium">
            {config.parameter_ranges.length}
          </div>
        </div>
        <div>
          <div className="text-slate-500 text-xs">总组合数</div>
          <div className="text-slate-200 font-medium">
            {totalCombinations.toLocaleString()}
          </div>
        </div>
        <div>
          <div className="text-slate-500 text-xs">采样次数</div>
          <div className="text-sky-400 font-medium">
            {config.random_samples}
          </div>
        </div>
        <div>
          <div className="text-slate-500 text-xs">预计返回</div>
          <div className="text-emerald-400 font-medium">
            Top {config.top_n_candidates}
          </div>
        </div>
      </div>
    </Card>
  );
}
