"""
Prediction & Assessment Routes: Handlers for supervised Type 2 Diabetes and Cardiovascular
Disease machine learning inference, SHAP Explainable AI attribution, and personalized reports.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from forms import DiabetesAssessmentForm, HeartAssessmentForm
from services.prediction_service import PredictionService
from models import UserProfile

prediction_bp = Blueprint('prediction', __name__)


@prediction_bp.route('/assessment')
@login_required
def index():
    """Main Risk Assessment Center: Overview, active models, and patient assessment history."""
    history = PredictionService.get_user_history(current_user.id)
    diabetes_latest = next((h for h in history if h['condition_name'] == 'diabetes'), None)
    heart_latest = next((h for h in history if h['condition_name'] == 'cardiovascular'), None)

    return render_template(
        'assessment_hub.html',
        history=history,
        diabetes_latest=diabetes_latest,
        heart_latest=heart_latest
    )


@prediction_bp.route('/assessment/diabetes', methods=['GET', 'POST'])
@login_required
def assess_diabetes():
    """Form view and submission handler for Type 2 Diabetes supervised risk evaluation."""
    form = DiabetesAssessmentForm()

    # Pre-populate defaults from UserProfile on GET
    if request.method == 'GET':
        profile = UserProfile.query.filter_by(user_id=current_user.id).first()
        if profile:
            if profile.age:
                form.age.data = profile.age
            if profile.height_cm and profile.weight_kg:
                h_m = float(profile.height_cm) / 100.0
                calc_bmi = round(float(profile.weight_kg) / (h_m * h_m), 1)
                form.bmi.data = calc_bmi

    if form.validate_on_submit():
        payload = {
            'pregnancies': form.pregnancies.data or 0,
            'glucose': form.glucose.data,
            'blood_pressure': form.blood_pressure.data,
            'skin_thickness': form.skin_thickness.data,
            'insulin': form.insulin.data,
            'bmi': form.bmi.data,
            'diabetes_pedigree': form.diabetes_pedigree.data,
            'age': form.age.data
        }

        result = PredictionService.evaluate_diabetes_risk(
            user_id=current_user.id,
            feature_dict=payload,
            persist=True
        )

        flash(
            f"Diabetes risk evaluation complete ({result['risk_category']} - {result['risk_percentage']}%).",
            "success"
        )
        return redirect(url_for('prediction.view_result', result_id=result['prediction_id']))

    return render_template('assessment_diabetes.html', form=form)


@prediction_bp.route('/assessment/cardiovascular', methods=['GET', 'POST'])
@login_required
def assess_cardiovascular():
    """Form view and submission handler for Cardiovascular Disease supervised risk evaluation."""
    form = HeartAssessmentForm()

    if request.method == 'GET':
        profile = UserProfile.query.filter_by(user_id=current_user.id).first()
        if profile:
            if profile.age:
                form.age.data = profile.age
            if profile.gender:
                form.sex.data = '1' if profile.gender.lower() == 'male' else '0'

    if form.validate_on_submit():
        payload = {
            'age': form.age.data,
            'sex': int(form.sex.data),
            'chest_pain_type': int(form.chest_pain_type.data),
            'resting_bp': form.resting_bp.data,
            'cholesterol': form.cholesterol.data,
            'fasting_blood_sugar': int(form.fasting_blood_sugar.data),
            'resting_ecg': int(form.resting_ecg.data),
            'max_heart_rate': form.max_heart_rate.data,
            'exercise_angina': int(form.exercise_angina.data),
            'st_depression': form.st_depression.data,
            'st_slope': int(form.st_slope.data),
            'num_major_vessels': int(form.num_major_vessels.data)
        }

        result = PredictionService.evaluate_cardiovascular_risk(
            user_id=current_user.id,
            feature_dict=payload,
            persist=True
        )

        flash(
            f"Cardiovascular risk evaluation complete ({result['risk_category']} - {result['risk_percentage']}%).",
            "success"
        )
        return redirect(url_for('prediction.view_result', result_id=result['prediction_id']))

    return render_template('assessment_heart.html', form=form)


@prediction_bp.route('/assessment/result/<int:result_id>')
@login_required
def view_result(result_id):
    """Detailed clinical report view featuring SHAP local attribution and preventive action plan."""
    report = PredictionService.get_prediction_by_id(result_id, current_user.id)
    if not report:
        flash("Assessment report not found or unauthorized.", "danger")
        return redirect(url_for('prediction.index'))

    return render_template('assessment_result.html', report=report)


# =============================================================================
# RESTful API Endpoints
# =============================================================================

@prediction_bp.route('/api/v1/assessment/predict-diabetes', methods=['POST'])
@login_required
def api_predict_diabetes():
    """REST endpoint for Type 2 Diabetes inference."""
    data = request.get_json(silent=True) or {}
    required_keys = ['glucose', 'blood_pressure', 'bmi', 'age']
    for k in required_keys:
        if k not in data:
            return jsonify({'success': False, 'error': f"Missing required feature: '{k}'"}), 400

    try:
        persist = data.get('persist', True)
        result = PredictionService.evaluate_diabetes_risk(
            user_id=current_user.id,
            feature_dict=data,
            persist=persist
        )
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@prediction_bp.route('/api/v1/assessment/predict-heart', methods=['POST'])
@login_required
def api_predict_heart():
    """REST endpoint for Cardiovascular Disease inference."""
    data = request.get_json(silent=True) or {}
    required_keys = ['age', 'sex', 'resting_bp', 'cholesterol', 'max_heart_rate']
    for k in required_keys:
        if k not in data:
            return jsonify({'success': False, 'error': f"Missing required feature: '{k}'"}), 400

    try:
        persist = data.get('persist', True)
        result = PredictionService.evaluate_cardiovascular_risk(
            user_id=current_user.id,
            feature_dict=data,
            persist=persist
        )
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@prediction_bp.route('/api/v1/assessment/history', methods=['GET'])
@login_required
def api_history():
    """REST endpoint to fetch historical risk evaluations."""
    condition = request.args.get('condition')
    history = PredictionService.get_user_history(current_user.id, condition=condition)
    return jsonify({'success': True, 'history': history})
