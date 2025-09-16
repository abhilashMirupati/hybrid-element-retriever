"""
Test cases for MarkupLM integration in HER framework.

This module tests the MarkupLM-enhanced no-semantic mode with hierarchical context.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from her.embeddings.markuplm_snippet_scorer import MarkupLMSnippetScorer, SnippetScore
from her.descriptors.markuplm_hierarchy_builder import MarkupLMHierarchyBuilder
from her.locator.markuplm_no_semantic import MarkupLMNoSemanticMatcher
from her.utils.xpath_generator import generate_xpath_candidates, XPathCandidate
from her.core.config_service import get_config_service


class TestMarkupLMSnippetScorer:
    """Test cases for MarkupLM snippet scorer."""
    
    def test_initialization(self):
        """Test MarkupLM scorer initialization."""
        # Mock the MarkupLM imports to avoid requiring the actual model
        with patch('her.embeddings.markuplm_snippet_scorer.MarkupLMProcessor') as mock_processor, \
             patch('her.embeddings.markuplm_snippet_scorer.MarkupLMForQuestionAnswering') as mock_model:
            
            # Mock the processor and model
            mock_processor.from_pretrained.return_value = Mock()
            mock_model.from_pretrained.return_value = Mock()
            
            scorer = MarkupLMSnippetScorer()
            assert scorer is not None
            assert scorer.is_available()
    
    def test_score_snippets_basic(self):
        """Test basic snippet scoring."""
        with patch('her.embeddings.markuplm_snippet_scorer.MarkupLMProcessor') as mock_processor, \
             patch('her.embeddings.markuplm_snippet_scorer.MarkupLMForQuestionAnswering') as mock_model:
            
            # Mock the processor and model
            mock_processor.from_pretrained.return_value = Mock()
            mock_model.from_pretrained.return_value = Mock()
            
            scorer = MarkupLMSnippetScorer()
            
            # Test data
            candidates = [
                {
                    'element': {
                        'tag': 'button',
                        'text': 'Apple',
                        'attributes': {'id': 'apple-btn'}
                    }
                }
            ]
            query = 'Click on "Apple" filter'
            
            # Mock the scoring method
            with patch.object(scorer, '_score_with_markuplm', return_value=[0.8]):
                results = scorer.score_snippets(candidates, query)
                
                assert len(results) == 1
                assert isinstance(results[0], SnippetScore)
                assert results[0].score == 0.8
                assert results[0].element['tag'] == 'button'
    
    def test_build_hierarchical_html(self):
        """Test hierarchical HTML building."""
        with patch('her.embeddings.markuplm_snippet_scorer.MarkupLMProcessor') as mock_processor, \
             patch('her.embeddings.markuplm_snippet_scorer.MarkupLMForQuestionAnswering') as mock_model:
            
            mock_processor.from_pretrained.return_value = Mock()
            mock_model.from_pretrained.return_value = Mock()
            
            scorer = MarkupLMSnippetScorer()
            
            # Test candidate with hierarchical context
            candidate = {
                'element': {
                    'tag': 'button',
                    'text': 'Apple',
                    'attributes': {'id': 'apple-btn', 'class': 'filter-button'}
                },
                'parents': [
                    {
                        'tag': 'div',
                        'attributes': {'class': 'filter-container'}
                    }
                ],
                'siblings': [
                    {
                        'tag': 'button',
                        'text': 'Samsung',
                        'attributes': {'id': 'samsung-btn'}
                    }
                ]
            }
            
            html = scorer._build_hierarchical_html(candidate)
            
            assert '<div class="filter-container">' in html
            assert '<button id="apple-btn" class="filter-button">Apple</button>' in html
            assert 'sibling-context' in html


class TestMarkupLMHierarchyBuilder:
    """Test cases for MarkupLM hierarchy builder."""
    
    def test_initialization(self):
        """Test hierarchy builder initialization."""
        builder = MarkupLMHierarchyBuilder()
        assert builder is not None
        assert builder.max_depth == 5
        assert builder.max_siblings == 5
    
    def test_build_context_for_candidates(self):
        """Test building context for candidates."""
        builder = MarkupLMHierarchyBuilder()
        
        # Test data
        candidates = [
            {
                'tag': 'button',
                'text': 'Apple',
                'attributes': {'id': 'apple-btn'},
                'xpath': '//div[@class="filters"]/button[@id="apple-btn"]'
            }
        ]
        
        all_elements = [
            {
                'tag': 'div',
                'attributes': {'class': 'filters'},
                'xpath': '//div[@class="filters"]'
            },
            {
                'tag': 'button',
                'text': 'Apple',
                'attributes': {'id': 'apple-btn'},
                'xpath': '//div[@class="filters"]/button[@id="apple-btn"]'
            },
            {
                'tag': 'button',
                'text': 'Samsung',
                'attributes': {'id': 'samsung-btn'},
                'xpath': '//div[@class="filters"]/button[@id="samsung-btn"]'
            }
        ]
        
        enhanced_candidates = builder.build_context_for_candidates(candidates, all_elements)
        
        assert len(enhanced_candidates) == 1
        enhanced = enhanced_candidates[0]
        
        assert 'parents' in enhanced
        assert 'siblings' in enhanced
        assert 'hierarchy_path' in enhanced
        assert 'html_context' in enhanced


class TestMarkupLMNoSemanticMatcher:
    """Test cases for MarkupLM no-semantic matcher."""
    
    def test_initialization(self):
        """Test matcher initialization."""
        with patch('her.locator.markuplm_no_semantic.MarkupLMSnippetScorer') as mock_scorer:
            mock_scorer.return_value = Mock()
            mock_scorer.return_value.is_available.return_value = True
            
            matcher = MarkupLMNoSemanticMatcher()
            assert matcher is not None
            assert matcher.is_markup_available()
    
    def test_query_basic(self):
        """Test basic query functionality."""
        with patch('her.locator.markuplm_no_semantic.MarkupLMSnippetScorer') as mock_scorer:
            mock_scorer.return_value = Mock()
            mock_scorer.return_value.is_available.return_value = True
            
            matcher = MarkupLMNoSemanticMatcher()
            
            # Test data
            elements = [
                {
                    'tag': 'button',
                    'text': 'Apple',
                    'attributes': {'id': 'apple-btn'},
                    'visible': True
                }
            ]
            query = 'Click on "Apple" filter'
            
            # Mock the scoring method
            with patch.object(matcher, '_score_with_markuplm', return_value=[]):
                result = matcher.query(query, elements)
                
                assert 'xpath' in result
                assert 'confidence' in result
                assert 'strategy' in result
    
    def test_find_initial_candidates(self):
        """Test finding initial candidates."""
        with patch('her.locator.markuplm_no_semantic.MarkupLMSnippetScorer') as mock_scorer:
            mock_scorer.return_value = Mock()
            mock_scorer.return_value.is_available.return_value = True
            
            matcher = MarkupLMNoSemanticMatcher()
            
            # Test data
            elements = [
                {
                    'tag': 'button',
                    'text': 'Apple',
                    'attributes': {'id': 'apple-btn'},
                    'visible': True
                },
                {
                    'tag': 'div',
                    'text': 'Some other text',
                    'attributes': {},
                    'visible': True
                }
            ]
            
            # Mock intent parser
            from her.locator.intent_parser import ParsedIntent, IntentType
            parsed_intent = ParsedIntent(
                original_step='Click on "Apple" filter',
                intent=IntentType.CLICK,
                target_text='Apple',
                value=None
            )
            
            with patch.object(matcher.intent_parser, 'parse_step', return_value=parsed_intent):
                candidates = matcher._find_initial_candidates(elements, parsed_intent)
                
                # Should find the button with "Apple" text
                assert len(candidates) >= 1
                assert any(c['text'] == 'Apple' for c in candidates)


class TestXPathGeneration:
    """Test cases for XPath generation."""
    
    def test_generate_xpath_candidates(self):
        """Test generating XPath candidates."""
        element = {
            'tag': 'button',
            'text': 'Apple',
            'attributes': {
                'id': 'apple-btn',
                'class': 'filter-button',
                'data-testid': 'apple-filter'
            }
        }
        
        candidates = generate_xpath_candidates(element)
        
        assert len(candidates) > 0
        
        # Check for ID-based XPath
        id_candidates = [c for c in candidates if c.strategy == 'id_based']
        assert len(id_candidates) == 1
        assert id_candidates[0].xpath == "//*[@id='apple-btn']"
        assert id_candidates[0].confidence == 1.0
        
        # Check for testid-based XPath
        testid_candidates = [c for c in candidates if c.strategy == 'testid_based']
        assert len(testid_candidates) == 1
        assert testid_candidates[0].xpath == "//*[@data-testid='apple-filter']"
    
    def test_generate_hierarchical_xpath(self):
        """Test generating hierarchical XPath."""
        from her.utils.xpath_generator import generate_hierarchical_xpath
        
        element = {
            'tag': 'button',
            'text': 'Apple',
            'attributes': {'id': 'apple-btn'}
        }
        
        hierarchy_context = {
            'hierarchy_path': ['div', 'div[1]', 'button[2]']
        }
        
        xpath = generate_hierarchical_xpath(element, hierarchy_context)
        
        assert xpath is not None
        assert 'div' in xpath
        assert 'button' in xpath
    
    def test_generate_combined_xpath(self):
        """Test generating combined XPath."""
        from her.utils.xpath_generator import generate_combined_xpath
        
        element = {
            'tag': 'button',
            'text': 'Apple',
            'attributes': {
                'class': 'filter-button',
                'type': 'button'
            }
        }
        
        xpath = generate_combined_xpath(element)
        
        assert xpath is not None
        assert 'button' in xpath
        assert 'class' in xpath


class TestIntegration:
    """Integration test cases."""
    
    def test_end_to_end_workflow(self):
        """Test end-to-end workflow with mocked MarkupLM."""
        with patch('her.locator.markuplm_no_semantic.MarkupLMSnippetScorer') as mock_scorer:
            # Mock the scorer
            mock_scorer.return_value = Mock()
            mock_scorer.return_value.is_available.return_value = True
            mock_scorer.return_value.score_snippets.return_value = [
                SnippetScore(
                    snippet='<button id="apple-btn">Apple</button>',
                    score=0.9,
                    xpath='//button[@id="apple-btn"]',
                    element={'tag': 'button', 'text': 'Apple', 'attributes': {'id': 'apple-btn'}},
                    confidence=0.9,
                    reasons=['high_markuplm_score', 'interactive_element']
                )
            ]
            
            # Create matcher
            matcher = MarkupLMNoSemanticMatcher()
            
            # Test data
            elements = [
                {
                    'tag': 'button',
                    'text': 'Apple',
                    'attributes': {'id': 'apple-btn', 'class': 'filter-button'},
                    'visible': True,
                    'xpath': '//button[@id="apple-btn"]'
                },
                {
                    'tag': 'a',
                    'text': 'Apple',
                    'attributes': {'href': '/apple'},
                    'visible': True,
                    'xpath': '//a[@href="/apple"]'
                }
            ]
            
            query = 'Click on "Apple" filter'
            
            # Execute query
            result = matcher.query(query, elements)
            
            # Verify result
            assert result['xpath'] is not None
            assert result['confidence'] > 0
            assert result['strategy'] == 'markuplm-enhanced'
            assert 'reasons' in result


def test_configuration():
    """Test configuration setup."""
    # Set environment variables
    import os
    os.environ["HER_USE_SEMANTIC_SEARCH"] = "false"
    os.environ["HER_USE_HIERARCHY"] = "true"
    os.environ["HER_USE_MARKUPLM_NO_SEMANTIC"] = "true"
    
    # Test configuration
    config_service = get_config_service()
    
    assert not config_service.should_use_semantic_search()
    assert config_service.should_use_hierarchy()
    assert config_service.should_use_markuplm_no_semantic()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])