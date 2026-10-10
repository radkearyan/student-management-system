import os
import pickle
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model.pkl')

def predict_performance(attendance_pct, average_marks):
    """
    Predicts student performance risk classification and confidence intervals
    based on attendance rate and average grades.
    """
    if not os.path.exists(MODEL_PATH):
        # Lazy training if the serialized file isn't compiled
        from backend.ai.train_model import train_model
        train_model()
        
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
        
    X_test = np.array([[attendance_pct, average_marks]])
    prediction = str(model.predict(X_test)[0])
    
    classes = model.classes_
    probabilities = model.predict_proba(X_test)[0]
    
    prob_dict = {str(classes[i]): float(probabilities[i]) for i in range(len(classes))}
    perf_score = float((attendance_pct * 0.3) + (average_marks * 0.7))
    
    suggestion = ""
    if prediction == "High Risk":
        if attendance_pct < 75:
            suggestion = "Critical: Immediate intervention required. Attendance is critically low. Student must attend extra remedial classes and clear pending lectures."
        else:
            suggestion = "Critical: Student is attending classes but scoring very low. Suggesting 1-on-1 tutoring sessions and basic concept clearing assignments."
    elif prediction == "Moderate Risk":
        if attendance_pct < 75:
            suggestion = "Warning: Attendance is below 75%. Improve classroom attendance to restore academic momentum. Watch online lectures."
        else:
            suggestion = "Warning: Performance is average. Encourage revision of mock examinations and participation in peer study groups."
    else:
        suggestion = "Excellent: Keep up the good work. Highly encourage taking advanced elective projects or assisting peers as a tutor."

    return {
        "status": prediction,
        "probabilities": prob_dict,
        "performance_score": round(perf_score, 1),
        "suggestion": suggestion
    }
