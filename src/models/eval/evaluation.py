"""
Fashion compatibility model evaluation module
"""

import os
import sys
import json
import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score, ndcg_score
from sklearn.metrics.pairwise import cosine_similarity
import warnings

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'train'))

from model_training import FashionCLIPModel
from inference import FashionStylist

warnings.filterwarnings('ignore')


class FashionEvaluator:
    """
    Fashion compatibility model evaluator
    """
    
    def __init__(self, model_path: str, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        """
        Initialize evaluator
        
        Args:
            model_path: Path to trained model
            device: Device to run on
        """
        self.device = device
        self.model = self._load_model(model_path)
        self.stylist = FashionStylist(model_path, device)
        
        # Store evaluation results
        self.evaluation_results = {}
        
        print(f"📊 Fashion Evaluator initialized on {device}")
    
    def _load_model(self, model_path: str) -> FashionCLIPModel:
        """Load trained model"""
        model = FashionCLIPModel()
        
        if os.path.exists(model_path):
            checkpoint = torch.load(model_path, map_location=self.device)
            model.load_state_dict(checkpoint['model_state_dict'])
            print(f"✅ Model loaded from {model_path}")
        else:
            print(f"⚠️ Model file not found at {model_path}, using untrained model")
        
        model.to(self.device)
        model.eval()
        return model
    
    def evaluate_triplet_accuracy(self, dataloader, num_batches: int = 100) -> Dict:
        """
        Evaluate Triplet Accuracy
        
        Args:
            dataloader: Test data loader
            num_batches: Number of batches to evaluate
            
        Returns:
            Evaluation results dictionary
        """
        print("🎯 Evaluating Triplet Accuracy...")
        
        total_correct = 0
        total_samples = 0
        distances = []
        
        with torch.no_grad():
            for i, batch in enumerate(dataloader):
                if i >= num_batches:
                    break
                    
                anchor, positive, negative = batch
                anchor = anchor.to(self.device)
                positive = positive.to(self.device)
                negative = negative.to(self.device)
                
                # Extract features
                anchor_feat = self.model(anchor)
                positive_feat = self.model(positive)
                negative_feat = self.model(negative)
                
                # Calculate distances
                pos_dist = torch.norm(anchor_feat - positive_feat, dim=1)
                neg_dist = torch.norm(anchor_feat - negative_feat, dim=1)
                
                # Calculate accuracy
                correct = (pos_dist < neg_dist).sum().item()
                total_correct += correct
                total_samples += anchor.size(0)
                
                # Record distance distribution
                distances.extend([
                    ('positive', d.item()) for d in pos_dist
                ] + [
                    ('negative', d.item()) for d in neg_dist
                ])
        
        accuracy = total_correct / total_samples if total_samples > 0 else 0
        
        # Analyze distance distribution
        pos_distances = [d[1] for d in distances if d[0] == 'positive']
        neg_distances = [d[1] for d in distances if d[0] == 'negative']
        
        results = {
            'triplet_accuracy': accuracy,
            'total_samples': total_samples,
            'positive_distances': {
                'mean': np.mean(pos_distances) if pos_distances else 0,
                'std': np.std(pos_distances) if pos_distances else 0
            },
            'negative_distances': {
                'mean': np.mean(neg_distances) if neg_distances else 0,
                'std': np.std(neg_distances) if neg_distances else 0
            }
        }
        
        self.evaluation_results['triplet_accuracy'] = results
        return results
    
    def evaluate_recommendation_quality(self, test_data: List[Dict], num_recommendations: int = 10) -> Dict:
        """
        Evaluate recommendation quality
        
        Args:
            test_data: Test data with real compatibility relationships
            num_recommendations: Number of recommendations
            
        Returns:
            Recommendation quality evaluation results
        """
        print("🎯 Evaluating Recommendation Quality...")
        
        # Load data
        self.stylist.load_farfetch_database()
        
        # Simulate user wardrobe
        user_wardrobe = []
        for i, item in enumerate(test_data[:20]):  # Use first 20 as user wardrobe
            user_wardrobe.append({
                'id': f'user_item_{i}',
                'image_path': item.get('image_path', ''),
                'category': item.get('category', 'unknown')
            })
        
        self.stylist.user_wardrobe = user_wardrobe
        
        # Evaluation metrics
        precision_scores = []
        recall_scores = []
        f1_scores = []
        ndcg_scores = []
        
        for item in test_data[20:50]:  # Test on remaining items
            try:
                # Get recommendations
                recommendations = self.stylist.recommend_from_wardrobe(
                    item_id=item.get('id', ''),
                    num_recommendations=num_recommendations
                )
                
                if not recommendations:
                    continue
                
                # Calculate recommendation quality metrics
                metrics = self._calculate_recommendation_metrics(
                    item, recommendations, test_data
                )
                
                precision_scores.append(metrics['precision'])
                recall_scores.append(metrics['recall'])
                f1_scores.append(metrics['f1'])
                ndcg_scores.append(metrics['ndcg'])
                
            except Exception as e:
                print(f"Error evaluating item {item.get('id', '')}: {e}")
                continue
        
        results = {
            'precision': np.mean(precision_scores) if precision_scores else 0,
            'recall': np.mean(recall_scores) if recall_scores else 0,
            'f1_score': np.mean(f1_scores) if f1_scores else 0,
            'ndcg': np.mean(ndcg_scores) if ndcg_scores else 0,
            'num_evaluated': len(precision_scores)
        }
        
        self.evaluation_results['recommendation_quality'] = results
        return results
    
    def _calculate_recommendation_metrics(self, target_item: Dict, recommendations: List[Dict], test_data: List[Dict]) -> Dict:
        """Calculate evaluation metrics for a single recommendation"""
        
        # Get ground truth relevant items (based on category and brand)
        target_category = target_item.get('category', '')
        target_brand = target_item.get('brand', '')
        
        relevant_items = []
        for item in test_data:
            if (item.get('category', '') == target_category or 
                item.get('brand', '') == target_brand):
                relevant_items.append(item.get('id', ''))
        
        # Calculate recommendation relevance
        recommended_ids = [rec.get('id', '') for rec in recommendations]
        relevant_recommended = [rid for rid in recommended_ids if rid in relevant_items]
        
        # Calculate metrics
        precision = len(relevant_recommended) / len(recommended_ids) if recommended_ids else 0
        recall = len(relevant_recommended) / len(relevant_items) if relevant_items else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        # Calculate NDCG
        ndcg = self._calculate_ndcg(recommended_ids, relevant_items)
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'ndcg': ndcg
        }
    
    def _calculate_ndcg(self, recommended_ids: List[str], relevant_items: List[str], k: int = 10) -> float:
        """Calculate NDCG@k"""
        
        # Simplified NDCG calculation
        dcg = 0
        for i, item_id in enumerate(recommended_ids[:k]):
            if item_id in relevant_items:
                dcg += 1 / np.log2(i + 2)  # i+2 because log2(1) = 0
        
        # Ideal DCG
        idcg = 0
        for i in range(min(len(relevant_items), k)):
            idcg += 1 / np.log2(i + 2)
        
        return dcg / idcg if idcg > 0 else 0
    
    def evaluate_fashion_compatibility(self, compatibility_pairs: List[Tuple[str, str, bool]]) -> Dict:
        """
        Evaluate fashion compatibility judgment ability
        
        Args:
            compatibility_pairs: List of compatibility pairs [(item1_id, item2_id, is_compatible), ...]
            
        Returns:
            Compatibility evaluation results
        """
        print("🎯 Evaluating Fashion Compatibility...")
        
        # Load data
        self.stylist.load_farfetch_database()
        
        predictions = []
        ground_truth = []
        
        for item1_id, item2_id, is_compatible in compatibility_pairs:
            try:
                # Get item features
                feat1 = self.stylist._extract_features(item1_id)
                feat2 = self.stylist._extract_features(item2_id)
                
                if feat1 is None or feat2 is None:
                    continue
                
                # Calculate similarity
                similarity = cosine_similarity(
                    feat1.reshape(1, -1), 
                    feat2.reshape(1, -1)
                )[0][0]
                
                # Predict compatibility (similarity threshold)
                predicted_compatible = similarity > 0.5
                
                predictions.append(predicted_compatible)
                ground_truth.append(is_compatible)
                
            except Exception as e:
                print(f"Error evaluating pair ({item1_id}, {item2_id}): {e}")
                continue
        
        if not predictions:
            return {'error': 'No valid predictions made'}
        
        # Calculate classification metrics
        precision, recall, f1, _ = precision_recall_fscore_support(
            ground_truth, predictions, average='binary'
        )
        
        # Calculate AUC
        try:
            auc = roc_auc_score(ground_truth, predictions)
        except:
            auc = 0.5  # Random performance
        
        results = {
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'auc': auc,
            'num_pairs': len(predictions)
        }
        
        self.evaluation_results['fashion_compatibility'] = results
        return results
    
    def _get_item_features(self, item_id: str) -> Optional[np.ndarray]:
        """Get item features"""
        try:
            return self.stylist._extract_features(item_id)
        except:
            return None
    
    def generate_report(self, save_path: str = "evaluation_report.json") -> Dict:
        """Generate comprehensive evaluation report"""
        
        print("📊 Generating evaluation report...")
        
        # Combine all results
        report = {
            'evaluation_summary': self._generate_summary(),
            'detailed_results': self.evaluation_results,
            'timestamp': str(pd.Timestamp.now())
        }
        
        # Save report
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Generate visualization
        self._plot_evaluation_results()
        
        return report
    
    def _generate_summary(self) -> Dict:
        """Generate evaluation summary"""
        summary = {}
        
        if 'triplet_accuracy' in self.evaluation_results:
            acc = self.evaluation_results['triplet_accuracy']['triplet_accuracy']
            summary['triplet_accuracy'] = f"{acc:.3f}"
            summary['triplet_performance'] = "Excellent" if acc > 0.85 else "Good" if acc > 0.7 else "Needs Improvement"
        
        if 'recommendation_quality' in self.evaluation_results:
            rec = self.evaluation_results['recommendation_quality']
            summary['recommendation_f1'] = f"{rec['f1_score']:.3f}"
            summary['recommendation_ndcg'] = f"{rec['ndcg']:.3f}"
        
        if 'fashion_compatibility' in self.evaluation_results:
            comp = self.evaluation_results['fashion_compatibility']
            summary['compatibility_auc'] = f"{comp['auc']:.3f}"
            summary['compatibility_f1'] = f"{comp['f1_score']:.3f}"
        
        return summary
    
    def _plot_evaluation_results(self, save_path: str = "evaluation_plots.png"):
        """Plot evaluation results"""
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Fashion Model Evaluation Results', fontsize=16)
        
        # Triplet accuracy
        if 'triplet_accuracy' in self.evaluation_results:
            acc = self.evaluation_results['triplet_accuracy']['triplet_accuracy']
            axes[0, 0].bar(['Triplet Accuracy'], [acc], color='skyblue')
            axes[0, 0].set_ylim(0, 1)
            axes[0, 0].set_title('Triplet Accuracy')
            axes[0, 0].text(0, acc + 0.02, f'{acc:.3f}', ha='center')
        
        # Recommendation quality
        if 'recommendation_quality' in self.evaluation_results:
            rec = self.evaluation_results['recommendation_quality']
            metrics = ['Precision', 'Recall', 'F1', 'NDCG']
            values = [rec['precision'], rec['recall'], rec['f1_score'], rec['ndcg']]
            axes[0, 1].bar(metrics, values, color='lightgreen')
            axes[0, 1].set_ylim(0, 1)
            axes[0, 1].set_title('Recommendation Quality')
            for i, v in enumerate(values):
                axes[0, 1].text(i, v + 0.02, f'{v:.3f}', ha='center')
        
        # Fashion compatibility
        if 'fashion_compatibility' in self.evaluation_results:
            comp = self.evaluation_results['fashion_compatibility']
            metrics = ['Precision', 'Recall', 'F1', 'AUC']
            values = [comp['precision'], comp['recall'], comp['f1_score'], comp['auc']]
            axes[1, 0].bar(metrics, values, color='lightcoral')
            axes[1, 0].set_ylim(0, 1)
            axes[1, 0].set_title('Fashion Compatibility')
            for i, v in enumerate(values):
                axes[1, 0].text(i, v + 0.02, f'{v:.3f}', ha='center')
        
        # Overall performance
        overall_score = 0
        count = 0
        if 'triplet_accuracy' in self.evaluation_results:
            overall_score += self.evaluation_results['triplet_accuracy']['triplet_accuracy']
            count += 1
        if 'recommendation_quality' in self.evaluation_results:
            overall_score += self.evaluation_results['recommendation_quality']['f1_score']
            count += 1
        if 'fashion_compatibility' in self.evaluation_results:
            overall_score += self.evaluation_results['fashion_compatibility']['f1_score']
            count += 1
        
        if count > 0:
            overall_score /= count
            axes[1, 1].bar(['Overall Score'], [overall_score], color='gold')
            axes[1, 1].set_ylim(0, 1)
            axes[1, 1].set_title('Overall Performance')
            axes[1, 1].text(0, overall_score + 0.02, f'{overall_score:.3f}', ha='center')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Evaluation plots saved to {save_path}")


def create_test_data() -> List[Dict]:
    """Create test data for evaluation"""
    
    # Here you can create some test data
    # In actual use, you should have a real test set
    
    test_data = []
    # Simulate some test data
    for i in range(100):
        test_data.append({
            'id': f'test_item_{i}',
            'category': f'category_{i % 10}',
            'brand': f'brand_{i % 5}',
            'image_path': f'../data/images/test_{i}.jpg'  # Assumed path
        })
    
    return test_data


def main():
    """Main evaluation function"""
    
    # Initialize evaluator
    model_path = "../train/checkpoints/best_model.pth"  # Adjust path as needed
    evaluator = FashionEvaluator(model_path)
    
    # Create test data
    test_data = create_test_data()
    
    # 1. Evaluate Triplet Accuracy
    print("=" * 50)
    print("1. Triplet Accuracy Evaluation")
    print("=" * 50)
    
    # You need to create a dataloader for this
    # triplet_results = evaluator.evaluate_triplet_accuracy(test_dataloader)
    
    # 2. Evaluate recommendation quality
    print("=" * 50)
    print("2. Recommendation Quality Evaluation")
    print("=" * 50)
    
    rec_results = evaluator.evaluate_recommendation_quality(test_data)
    print(f"Recommendation F1: {rec_results['f1_score']:.3f}")
    print(f"Recommendation NDCG: {rec_results['ndcg']:.3f}")
    
    # 3. Evaluate fashion compatibility
    print("=" * 50)
    print("3. Fashion Compatibility Evaluation")
    print("=" * 50)
    
    # Create some compatibility test pairs
    compatibility_pairs = []
    for i in range(50):
        item1_id = f'test_item_{i}'
        item2_id = f'test_item_{i + 10}'
        is_compatible = (i % 3 == 0)  # Simulate compatibility
        compatibility_pairs.append((item1_id, item2_id, is_compatible))
    
    comp_results = evaluator.evaluate_fashion_compatibility(compatibility_pairs)
    print(f"Compatibility AUC: {comp_results['auc']:.3f}")
    print(f"Compatibility F1: {comp_results['f1_score']:.3f}")
    
    # 4. Generate evaluation report
    print("=" * 50)
    print("4. Generating Report")
    print("=" * 50)
    
    report = evaluator.generate_report()
    
    # Print summary
    print("\n📊 Evaluation Summary:")
    for key, value in report['evaluation_summary'].items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
