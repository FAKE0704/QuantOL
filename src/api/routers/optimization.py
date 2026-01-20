"""
Optimization router for FastAPI.

Provides RESTful API endpoints for parameter optimization:
- POST /api/optimization/start - Start parameter optimization
- GET /api/optimization/results/{optimization_id} - Get optimization results
- GET /api/optimization/list - List all optimizations
- GET /api/optimization/templates - List available rule templates
- GET /api/optimization/templates/{template_id} - Get specific template
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
import logging

from src.core.auth.jwt_service import JWTService
from src.services.optimization_service import OptimizationService, OptimizationConfig, OptimizationResult
from src.services.template_service import TemplateService, get_template, list_templates, PREDEFINED_TEMPLATES

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/optimization", tags=["optimization"])

# Security
security = HTTPBearer()

# In-memory storage for optimization results (in production, use Redis or database)
_optimization_results: Dict[str, OptimizationResult] = {}

# Pydantic models


class ParameterRangeModel(BaseModel):
    """Parameter range model."""
    indicator: str
    parameter_name: str
    type: str  # "range" or "custom"
    min: Optional[int] = None
    max: Optional[int] = None
    step: Optional[int] = None
    values: Optional[List[int]] = None


class OptimizationConfigModel(BaseModel):
    """Optimization configuration model."""
    parameter_ranges: List[ParameterRangeModel]

    # Scan method
    scan_method: str = "random"
    random_samples: int = 50

    # Screening configuration
    screening_period: Dict[str, str]  # {"start_date": "YYYYMMDD", "end_date": "YYYYMMDD"}
    screening_metric: str = "sharpe_ratio"
    top_n_candidates: int = 5

    # Performance thresholds (optional)
    performance_thresholds: Optional[Dict[str, Optional[float]]] = None


class BaseConfigModel(BaseModel):
    """Base backtest configuration model."""
    start_date: str  # Format: YYYYMMDD
    end_date: str  # Format: YYYYMMDD
    frequency: str
    symbols: List[str]
    initial_capital: float
    commission_rate: float
    slippage: float
    position_strategy: str
    position_params: Dict[str, Any]


class RuleTemplatesModel(BaseModel):
    """Rule templates model."""
    open_rule_template: Optional[str] = None
    close_rule_template: Optional[str] = None
    buy_rule_template: Optional[str] = None
    sell_rule_template: Optional[str] = None


class OptimizationRequest(BaseModel):
    """Optimization request model."""
    base_config: BaseConfigModel
    rule_templates: RuleTemplatesModel
    optimization_config: OptimizationConfigModel


class OptimizationResponse(BaseModel):
    """Optimization response model."""
    success: bool
    optimization_id: Optional[str] = None
    message: str
    data: Optional[Dict[str, Any]] = None


class OptimizationResultResponse(BaseModel):
    """Optimization result response model."""
    optimization_id: str
    status: str
    screening_results: Optional[List[Dict[str, Any]]] = None
    best_parameters: Optional[Dict[str, int]] = None
    best_metrics: Optional[Dict[str, float]] = None
    progress: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TemplateResponse(BaseModel):
    """Template response model."""
    template_id: str
    name: str
    description: Optional[str] = None
    open_rule_template: Optional[str] = None
    close_rule_template: Optional[str] = None
    buy_rule_template: Optional[str] = None
    sell_rule_template: Optional[str] = None
    variables: Dict[str, Dict[str, Any]]


class TemplatesListResponse(BaseModel):
    """Templates list response model."""
    success: bool
    message: str
    data: Optional[List[TemplateResponse]] = None


# Helper functions


def _convert_config_model_to_dict(config_model: OptimizationConfigModel) -> Dict[str, Any]:
    """Convert OptimizationConfigModel to dictionary."""
    return {
        "parameter_ranges": [
            {
                "indicator": pr.indicator,
                "parameter_name": pr.parameter_name,
                "type": pr.type,
                "min": pr.min,
                "max": pr.max,
                "step": pr.step,
                "values": pr.values
            }
            for pr in config_model.parameter_ranges
        ],
        "scan_method": config_model.scan_method,
        "random_samples": config_model.random_samples,
        "screening_start": config_model.screening_period.get("start_date", ""),
        "screening_end": config_model.screening_period.get("end_date", ""),
        "screening_metric": config_model.screening_metric,
        "top_n": config_model.top_n_candidates,
        "min_sharpe": config_model.performance_thresholds.get("min_sharpe") if config_model.performance_thresholds else None,
        "max_drawdown": config_model.performance_thresholds.get("max_drawdown_limit") if config_model.performance_thresholds else None,
        "min_win_rate": config_model.performance_thresholds.get("min_win_rate") if config_model.performance_thresholds else None,
    }


async def _run_optimization_task(
    optimization_id: str,
    request: OptimizationRequest
):
    """
    Background task to run optimization.

    Args:
        optimization_id: Unique optimization identifier
        request: Optimization request
    """
    import pandas as pd
    from src.core.strategy.backtesting import BacktestConfig
    from src.data.data_loader import DataLoader

    try:
        logger.info(f"Starting optimization task {optimization_id}")

        # Convert request to internal config
        opt_config_dict = _convert_config_model_to_dict(request.optimization_config)
        opt_config = OptimizationConfig(**opt_config_dict)

        # Create base backtest config
        base_config = BacktestConfig(
            start_date=request.base_config.start_date,
            end_date=request.base_config.end_date,
            target_symbol=request.base_config.symbols[0] if request.base_config.symbols else "",
            frequency=request.base_config.frequency,
            initial_capital=request.base_config.initial_capital,
            commission_rate=request.base_config.commission_rate,
            slippage=request.base_config.slippage,
            position_strategy_type=request.base_config.position_strategy,
            position_strategy_params=request.base_config.position_params,
            target_symbols=request.base_config.symbols
        )

        # Load data
        data_loader = DataLoader()
        data = await data_loader.load_data(
            symbols=request.base_config.symbols,
            start_date=request.base_config.start_date,
            end_date=request.base_config.end_date,
            frequency=request.base_config.frequency
        )

        if data is None or data.empty:
            raise ValueError("Failed to load data for optimization")

        # Create optimization service
        opt_service = OptimizationService()

        # Run optimization
        result = await opt_service.run_optimization(
            config=opt_config,
            rule_templates={
                k: v for k, v in {
                    "open_rule": request.rule_templates.open_rule_template,
                    "close_rule": request.rule_templates.close_rule_template,
                    "buy_rule": request.rule_templates.buy_rule_template,
                    "sell_rule": request.rule_templates.sell_rule_template
                }.items() if v is not None
            },
            base_config=base_config,
            data=data,
            progress_callback=lambda current, total, latest: logger.info(
                f"Optimization {optimization_id} progress: {current}/{total}"
            )
        )

        # Store result
        _optimization_results[optimization_id] = result

        logger.info(f"Optimization task {optimization_id} completed with status: {result.status}")

    except Exception as e:
        logger.error(f"Optimization task {optimization_id} failed: {e}")
        # Store failed result
        _optimization_results[optimization_id] = OptimizationResult(
            optimization_id=optimization_id,
            status="failed",
            error=str(e)
        )


# API endpoints


@router.post("/start", response_model=OptimizationResponse)
async def start_optimization(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Start parameter optimization.

    Args:
        request: Optimization request with base config, rule templates, and optimization config
        background_tasks: FastAPI background tasks
        credentials: Authorization credentials

    Returns:
        OptimizationResponse with optimization_id
    """
    try:
        # Validate request
        if not request.optimization_config.parameter_ranges:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No parameter ranges defined"
            )

        # Generate optimization ID
        optimization_id = f"opt_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Initialize with pending status
        _optimization_results[optimization_id] = OptimizationResult(
            optimization_id=optimization_id,
            status="pending"
        )

        # Add background task
        background_tasks.add_task(_run_optimization_task, optimization_id, request)

        return OptimizationResponse(
            success=True,
            optimization_id=optimization_id,
            message="Optimization task started",
            data={"optimization_id": optimization_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start optimization: {str(e)}"
        )


@router.get("/results/{optimization_id}", response_model=OptimizationResultResponse)
async def get_optimization_results(
    optimization_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get optimization results.

    Args:
        optimization_id: Optimization identifier
        credentials: Authorization credentials

    Returns:
        OptimizationResultResponse with screening results
    """
    if optimization_id not in _optimization_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Optimization {optimization_id} not found"
        )

    result = _optimization_results[optimization_id]

    return OptimizationResultResponse(
        optimization_id=result.optimization_id,
        status=result.status,
        screening_results=[r.to_dict() for r in result.screening_results] if result.screening_results else None,
        best_parameters=result.best_parameters,
        best_metrics=result.best_metrics,
        progress=result.progress,
        error=result.error
    )


@router.get("/list")
async def list_optimizations(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    List all optimizations.

    Args:
        credentials: Authorization credentials

    Returns:
        List of optimization summaries
    """
    return {
        "success": True,
        "message": "Retrieved optimization list",
        "data": [
            {
                "optimization_id": opt_id,
                "status": result.status,
                "created_at": opt_id.replace("opt_", ""),
                "best_metrics": result.best_metrics
            }
            for opt_id, result in _optimization_results.items()
        ]
    }


@router.get("/templates", response_model=TemplatesListResponse)
async def get_templates(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    List all available rule templates.

    Args:
        credentials: Authorization credentials

    Returns:
        TemplatesListResponse with all templates
    """
    try:
        templates = []
        for template_id, template_dict in PREDEFINED_TEMPLATES.items():
            templates.append(TemplateResponse(
                template_id=template_dict["template_id"],
                name=template_dict["name"],
                description=template_dict.get("description"),
                open_rule_template=template_dict.get("open_rule_template"),
                close_rule_template=template_dict.get("close_rule_template"),
                buy_rule_template=template_dict.get("buy_rule_template"),
                sell_rule_template=template_dict.get("sell_rule_template"),
                variables=template_dict.get("variables", {})
            ))

        return TemplatesListResponse(
            success=True,
            message=f"Retrieved {len(templates)} templates",
            data=templates
        )

    except Exception as e:
        logger.error(f"Failed to get templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get templates: {str(e)}"
        )


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template_by_id(
    template_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get a specific rule template.

    Args:
        template_id: Template identifier
        credentials: Authorization credentials

    Returns:
        TemplateResponse with template details
    """
    template = get_template(template_id)

    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found"
        )

    return TemplateResponse(
        template_id=template.template_id,
        name=template.name,
        description=template.description,
        open_rule_template=template.open_rule_template,
        close_rule_template=template.close_rule_template,
        buy_rule_template=template.buy_rule_template,
        sell_rule_template=template.sell_rule_template,
        variables={
            k: {
                "type": v.var_type,
                "default_value": v.default_value,
                "description": v.description
            }
            for k, v in template.variables.items()
        }
    )
