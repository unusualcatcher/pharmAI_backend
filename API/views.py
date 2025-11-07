from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
import json
import os
from typing import Dict, Any, Optional

def load_dataset() -> Optional[Dict[str, Any]]:
    file_path = os.path.join(settings.BASE_DIR, 'dataset.json')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            pharma_data = json.load(f)
        return pharma_data
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None
    except Exception:
        return None

def iqvia_api(request):
    area_query = request.GET.get('area')
    
    if not area_query:
        return JsonResponse({
            "error": "Missing 'area' query parameter.",
            "usage_example": "/api/iqvia?area=respiratory"
        }, status=400)
        
    area_key = area_query.lower()

    pharma_data = load_dataset()

    if pharma_data is None:
        return JsonResponse({"error": "Data file not found or could not be loaded on server."}, status=500)

    try:
        therapy_areas_data = pharma_data['market_intelligence_iqvia']['therapy_areas']
        
        if area_key not in therapy_areas_data:
            available_areas = list(therapy_areas_data.keys())
            return JsonResponse({
                "error": f"Therapy area '{area_query}' not found.",
                "available_areas": available_areas
            }, status=404)
            
        area_data = therapy_areas_data[area_key]

    except KeyError as e:
        return JsonResponse({"error": f"Data structure mismatch. Missing expected key: {e}"}, status=500)

    try:
        market_size = area_data.get('global_market_size_usd_millions')
        cagr = area_data.get('cagr_forecasted')
        forecast_period = area_data.get('forecast_period')
        
        disease_data = area_data.get('top_diseases', [])
        
        competitor_data = []
        for disease in disease_data:
            disease_market_size = disease.get('market_data', {}).get('market_size_usd_millions')
            players_raw = disease.get('market_data', {}).get('key_players_market_share', [])
            players = [
                {
                    "company": player.get('company'),
                    "market_share_percent": player.get('share_percent')
                }
                for player in players_raw
            ]
            
            competitor_data.append({
                "disease_name": disease.get('disease_name'),
                "disease_market_size_usd_millions": disease_market_size,
                "key_players": players
            })

        response_data = {
            "therapy_area": area_data.get('therapy_area_name', area_key),
            "global_market_size_usd_millions": market_size,
            "cagr_forecasted_percent": cagr,
            "forecast_period": forecast_period,
            "disease_markets_and_competitors": competitor_data
        }
        
        return JsonResponse(response_data, status=200, json_dumps_params={'indent': 2})

    except Exception as e:
        return JsonResponse({"error": f"An error occurred while processing data for '{area_key}': {str(e)}"}, status=500)

def clinical_trials_api(request):
    molecule_query = request.GET.get('molecule')

    if not molecule_query:
        return JsonResponse({
            "error": "Missing 'molecule' query parameter.",
            "usage_example": "/api/trials?molecule=pirfenidone"
        }, status=400)

    molecule_key = molecule_query.lower()
    
    pharma_data = load_dataset()

    if pharma_data is None:
        return JsonResponse({"error": "Data file not found or could not be loaded on server."}, status=500)

    try:
        trials_data = pharma_data['clinical_trials']
        
        if molecule_key not in trials_data:
            available_molecules = list(trials_data.keys())
            return JsonResponse({
                "error": f"Molecule '{molecule_query}' not found.",
                "available_molecules": available_molecules
            }, status=404)
            
        molecule_data = trials_data[molecule_key]

    except KeyError as e:
        return JsonResponse({"error": f"Data structure mismatch. Missing expected key: {e}"}, status=500)

    try:
        active_trials_raw = molecule_data.get('active_trials', [])
        
        ongoing_trials_and_sponsors = []
        for trial in active_trials_raw:
            ongoing_trials_and_sponsors.append({
                "nct_id": trial.get('nct_id'),
                "title": trial.get('title'),
                "phase": trial.get('phase'),
                "status": trial.get('status'),
                "sponsor": trial.get('sponsor'),
                "indication": trial.get('indication'),
                "enrollment": trial.get('enrollment'),
                "estimated_completion": trial.get('estimated_completion')
            })

        response_data = {
            "molecule_name": molecule_data.get('molecule_name'),
            "drug_class": molecule_data.get('drug_class'),
            "total_trials_reported": molecule_data.get('total_trials'),
            "active_trials_count": len(ongoing_trials_and_sponsors),
            "ongoing_trials_and_sponsors": ongoing_trials_and_sponsors,
            "sponsor_breakdown": molecule_data.get('sponsor_breakdown'),
            "indication_distribution": molecule_data.get('indication_distribution')
        }

        return JsonResponse(response_data, status=200, json_dumps_params={'indent': 2})

    except Exception as e:
        return JsonResponse({"error": f"An error occurred while processing data for '{molecule_key}': {str(e)}"}, status=500)
    
def exim_trade_api(request):
    molecule_query = request.GET.get('molecule')

    if not molecule_query:
        return JsonResponse({
            "error": "Missing 'molecule' query parameter.",
            "usage_example": "/api/exim-trade?molecule=metformin"
        }, status=400)

    molecule_key = molecule_query.lower()
    
    pharma_data = load_dataset()

    if pharma_data is None:
        return JsonResponse({"error": "Data file not found or could not be loaded on server."}, status=500)

    try:
        trade_data = pharma_data['exim_trade_data']
        
        if molecule_key not in trade_data:
            available_molecules = list(trade_data.keys())
            return JsonResponse({
                "error": f"Molecule '{molecule_query}' not found in trade data.",
                "available_molecules": available_molecules
            }, status=404)
            
        molecule_data = trade_data[molecule_key]

    except KeyError as e:
        return JsonResponse({"error": f"Data structure mismatch. Missing expected key: {e}"}, status=500)

    try:
        response_data = {
            "molecule_name": molecule_data.get('molecule_name'),
            "api_exports_2023": molecule_data.get('api_exports_2023'),
            "formulation_imports_2023": molecule_data.get('formulation_imports_2023'),
            "market_trend": molecule_data.get('market_trend'),
            "forecast_2024_2026": molecule_data.get('forecast_2024_2026')
        }

        return JsonResponse(response_data, status=200, json_dumps_params={'indent': 2})

    except Exception as e:
        return JsonResponse({"error": f"An error occurred while processing data for '{molecule_key}': {str(e)}"}, status=500)

def patent_landscape_api(request):
    molecule_query = request.GET.get('molecule')

    if not molecule_query:
        return JsonResponse({
            "error": "Missing 'molecule' query parameter.",
            "usage_example": "/api/patents?molecule=semaglutide"
        }, status=400)

    molecule_key = molecule_query.lower()
    
    pharma_data = load_dataset()

    if pharma_data is None:
        return JsonResponse({"error": "Data file not found or could not be loaded on server."}, status=500)

    try:
        patent_data = pharma_data['patent_landscape']
        
        if molecule_key not in patent_data:
            available_molecules = list(patent_data.keys())
            return JsonResponse({
                "error": f"Molecule '{molecule_query}' not found in patent landscape data.",
                "available_molecules": available_molecules
            }, status=404)
            
        molecule_data = patent_data[molecule_key]

    except KeyError as e:
        return JsonResponse({"error": f"Data structure mismatch. Missing expected key: {e}"}, status=500)

    try:
        response_data = {
            "molecule_name": molecule_data.get('molecule_name'),
            "molecule_details": molecule_data.get('molecule_details'),
            "base_molecule_patent_status": molecule_data.get('base_molecule_patent_status'),
            "fto_status": molecule_data.get('freedom_to_operate'),
            "active_patents_us": molecule_data.get('active_patents_us'),
            "key_expired_patents": molecule_data.get('key_expired_patents'),
            "innovation_trends": {
                "white_space_opportunities": molecule_data.get('white_space_opportunities'),
                "recommended_strategy": molecule_data.get('recommended_strategy')
            },
            "patent_counts": {
                "expired_patents_count": molecule_data.get('expired_patents_count')
            }
        }

        return JsonResponse(response_data, status=200, json_dumps_params={'indent': 2})

    except Exception as e:
        return JsonResponse({"error": f"An error occurred while processing data for '{molecule_key}': {str(e)}"}, status=500)

def _flatten_knowledge_base(kb_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts the nested knowledge base into a simple
    {doc_id: doc_data} lookup map.
    """
    doc_map = {}
    for category, sub_categories in kb_data.items():
        for doc_key, doc_data in sub_categories.items():
            if isinstance(doc_data, dict) and 'document_id' in doc_data:
                # Use the document_id as the key for fast lookup
                doc_map[doc_data['document_id']] = doc_data
    return doc_map

def internal_knowledge_base_api(request):
    doc_id_query = request.GET.get('doc_id')

    if not doc_id_query:
        return JsonResponse({
            "error": "Missing 'doc_id' query parameter.",
            "usage_example": "/api/knowledge-base?doc_id=STRAT-2024-001"
        }, status=400)
    
    pharma_data = load_dataset()

    if pharma_data is None:
        return JsonResponse({"error": "Data file not found or could not be loaded on server."}, status=500)

    try:
        kb_data = pharma_data['internal_knowledge_base']
        
        # This is the essential step
        doc_map = _flatten_knowledge_base(kb_data)
        
        if doc_id_query not in doc_map:
            available_docs = list(doc_map.keys())
            return JsonResponse({
                "error": f"Document ID '{doc_id_query}' not found.",
                "available_document_ids": available_docs
            }, status=404)
            
        document_data = doc_map[doc_id_query]
        
        response_data = {
            "document_metadata": document_data,
            "synthetic_pdf_url": f"/media/synthetic_pdfs/{document_data.get('document_id', 'doc')}.pdf"
        }

        return JsonResponse(response_data, status=200, json_dumps_params={'indent': 2})

    except KeyError as e:
        return JsonResponse({"error": f"Data structure mismatch. Missing expected key: {e}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred while processing data for doc '{doc_id_query}': {str(e)}"}, status=500)

def patent_analysis_api(request):
    molecule_query = request.GET.get('molecule')

    if not molecule_query:
        return JsonResponse({
            "error": "Missing 'molecule' query parameter.",
            "usage_example": "/api/patent-analysis?molecule=metformin"
        }, status=400)

    molecule_key = molecule_query.lower()
    
    pharma_data = load_dataset()

    if pharma_data is None:
        return JsonResponse({"error": "Data file not found or could not be loaded on server."}, status=500)

    try:
        patent_data = pharma_data['patent_analysis']
        
        if molecule_key not in patent_data:
            available_molecules = list(patent_data.keys())
            return JsonResponse({
                "error": f"Molecule '{molecule_query}' not found in patent analysis data.",
                "available_molecules": available_molecules
            }, status=404)
            
        molecule_data = patent_data[molecule_key]

    except KeyError as e:
        return JsonResponse({"error": f"Data structure mismatch. Missing expected key: {e}"}, status=500)

    try:
        response_data = {
            "molecule_name": molecule_data.get('molecule'),
            "molecule_details": molecule_data.get('molecule_details'),
            "fto_status": molecule_data.get('fto_status'),
            "active_patents_us": molecule_data.get('active_patents'),
            "key_expired_patents": molecule_data.get('key_expired_patents'),
            "innovation_trends": {
                "strategic_opportunity_analysis": molecule_data.get('strategic_opportunity_analysis'),
            },
            "patent_counts": {
                "total_active_family_count": molecule_data.get('total_active_family_count'),
                "total_expired_family_count": molecule_data.get('total_expired_family_count')
            }
        }

        return JsonResponse(response_data, status=200, json_dumps_params={'indent': 2})

    except Exception as e:
        return JsonResponse({"error": f"An error occurred while processing data for '{molecule_key}': {str(e)}"}, status=500)
