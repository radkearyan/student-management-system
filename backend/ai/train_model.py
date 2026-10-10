import os
import pickle
import numpy as np
from sklearn.tree import DecisionTreeClassifier

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model.pkl')

def train_model():
    print("Training AI performance prediction model...")
    # Generate synthetic training data
    np.random.seed(42)
    n_samples = 1000
    
    # Generate attendance from 40% to 100%
    attendance = np.random.uniform(40, 100, n_samples)
    
    # Generate average marks from 30% to 100%
    avg_marks = np.random.uniform(30, 100, n_samples)
    
    # Introduce noise and correlation:
    # Lower attendance generally leads to lower marks, but not always
    for i in range(n_samples):
        if attendance[i] < 60:
            avg_marks[i] = max(30, avg_marks[i] - np.random.uniform(10, 30))
            
    # Assign labels based on rules + random noise to simulate real-world variance
    labels = []
    for att, mark in zip(attendance, avg_marks):
        # Determine risk profile
        risk_score = (100 - att) * 0.4 + (100 - mark) * 0.6
        
        if risk_score > 35:
            labels.append("High Risk")
        elif risk_score > 18:
            labels.append("Moderate Risk")
        else:
            labels.append("Low Risk")
            
    X = np.column_stack((attendance, avg_marks))
    y = np.array(labels)
    
    # Train Decision Tree Classifier
    model = DecisionTreeClassifier(max_depth=4, random_state=42)
    model.fit(X, y)
    
    # Save model to disk
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    print("AI Model trained and saved successfully at:", MODEL_PATH)

if __name__ == '__main__':
    train_model()
