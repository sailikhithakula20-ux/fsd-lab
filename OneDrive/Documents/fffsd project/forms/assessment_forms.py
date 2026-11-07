"""
Clinical Assessment Forms: WTForms validation for Type 2 Diabetes and Cardiovascular Disease.
Pre-populated with user baseline biomarkers and enforces clinical range validity.
"""

from flask_wtf import FlaskForm
from wtforms import IntegerField, FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class DiabetesAssessmentForm(FlaskForm):
    """Input form for Type 2 Diabetes supervised machine learning evaluation."""
    glucose = IntegerField(
        'Fasting Plasma Glucose (mg/dL)',
        validators=[
            DataRequired(message="Fasting glucose is required."),
            NumberRange(min=50, max=350, message="Glucose must be within clinical range (50 - 350 mg/dL).")
        ],
        description="Standard fasting reference: Normal <100 mg/dL, Prediabetes 100-125, Diabetes ≥126."
    )
    blood_pressure = IntegerField(
        'Diastolic Blood Pressure (mm Hg)',
        validators=[
            DataRequired(message="Diastolic blood pressure is required."),
            NumberRange(min=40, max=200, message="Diastolic BP must be between 40 and 200 mm Hg.")
        ],
        description="Normal diastolic pressure is typically 60 - 80 mm Hg."
    )
    insulin = FloatField(
        '2-Hour Serum Insulin (mu U/ml)',
        validators=[
            DataRequired(message="Serum insulin is required."),
            NumberRange(min=0.0, max=800.0, message="Insulin level must be between 0 and 800 mu U/ml.")
        ],
        default=80.0,
        description="Normal adult post-glucose challenge reference is 16 - 166 mu U/ml."
    )
    bmi = FloatField(
        'Body Mass Index (BMI in kg/m²)',
        validators=[
            DataRequired(message="BMI is required."),
            NumberRange(min=12.0, max=70.0, message="BMI must be between 12.0 and 70.0 kg/m².")
        ],
        description="Calculated as weight(kg) / height(m)². Auto-derived from your health profile."
    )
    age = IntegerField(
        'Age (Years)',
        validators=[
            DataRequired(message="Age is required."),
            NumberRange(min=18, max=115, message="Age must be between 18 and 115.")
        ]
    )
    skin_thickness = FloatField(
        'Triceps Skinfold Thickness (mm)',
        validators=[
            DataRequired(message="Triceps skinfold is required."),
            NumberRange(min=0.0, max=99.0, message="Value must be between 0 and 99 mm.")
        ],
        default=23.0,
        description="Surrogate marker for subcutaneous adipose distribution."
    )
    pregnancies = IntegerField(
        'Number of Pregnancies (if applicable)',
        validators=[
            NumberRange(min=0, max=20, message="Pregnancies count must be between 0 and 20.")
        ],
        default=0,
        description="Leave 0 for male or non-pregnant individuals."
    )
    diabetes_pedigree = FloatField(
        'Diabetes Pedigree Genetic Score',
        validators=[
            DataRequired(message="Pedigree function score is required."),
            NumberRange(min=0.05, max=2.5, message="Score must be between 0.05 and 2.50.")
        ],
        default=0.45,
        description="Synthesis of familial diabetes incidence (0.1 to 0.4: low, 0.5 to 1.2: moderate, >1.2: high family history)."
    )
    submit = SubmitField('Run Diagnostic ML Inference')


class HeartAssessmentForm(FlaskForm):
    """Input form for Cardiovascular Disease (CVD) supervised machine learning evaluation."""
    age = IntegerField(
        'Age (Years)',
        validators=[
            DataRequired(message="Age is required."),
            NumberRange(min=18, max=115, message="Age must be between 18 and 115.")
        ]
    )
    sex = SelectField(
        'Biological Sex',
        choices=[('1', 'Male (1)'), ('0', 'Female (0)')],
        validators=[DataRequired(message="Biological sex is required.")]
    )
    chest_pain_type = SelectField(
        'Chest Pain Classification',
        choices=[
            ('0', 'Type 0: Typical Angina (Exertional retrosternal pressure)'),
            ('1', 'Type 1: Atypical Angina (Non-exertional chest discomfort)'),
            ('2', 'Type 2: Non-Anginal Discomfort (Musculoskeletal / Pleuritic)'),
            ('3', 'Type 3: Asymptomatic (No overt pain symptoms)')
        ],
        validators=[DataRequired(message="Chest pain classification is required.")]
    )
    resting_bp = IntegerField(
        'Resting Systolic Blood Pressure (mm Hg)',
        validators=[
            DataRequired(message="Resting systolic BP is required."),
            NumberRange(min=70, max=250, message="Systolic BP must be between 70 and 250 mm Hg.")
        ],
        default=120,
        description="Optimal systolic blood pressure is < 120 mm Hg."
    )
    cholesterol = IntegerField(
        'Serum Cholesterol (mg/dL)',
        validators=[
            DataRequired(message="Serum cholesterol is required."),
            NumberRange(min=100, max=600, message="Cholesterol must be between 100 and 600 mg/dL.")
        ],
        default=200,
        description="Desirable total cholesterol is < 200 mg/dL."
    )
    fasting_blood_sugar = SelectField(
        'Fasting Blood Sugar > 120 mg/dL',
        choices=[
            ('0', 'Normal / Controlled (≤ 120 mg/dL)'),
            ('1', 'Elevated (> 120 mg/dL)')
        ],
        validators=[DataRequired()]
    )
    resting_ecg = SelectField(
        'Resting Electrocardiogram (ECG)',
        choices=[
            ('0', 'Normal ECG trace'),
            ('1', 'ST-T Wave Abnormality (T-wave inversions / ST elevation)'),
            ('2', 'Left Ventricular Hypertrophy (Estes criteria)')
        ],
        validators=[DataRequired()]
    )
    max_heart_rate = IntegerField(
        'Maximum Heart Rate Achieved (bpm)',
        validators=[
            DataRequired(message="Maximum heart rate is required."),
            NumberRange(min=60, max=230, message="Heart rate must be between 60 and 230 bpm.")
        ],
        default=155,
        description="Peak heart rate achieved during physical stress or exertion."
    )
    exercise_angina = SelectField(
        'Exercise-Induced Angina',
        choices=[
            ('0', 'No exercise-induced ischemic pain'),
            ('1', 'Yes (Exertional chest constriction present)')
        ],
        validators=[DataRequired()]
    )
    st_depression = FloatField(
        'ST Depression (Oldpeak in mm)',
        validators=[
            DataRequired(message="ST depression is required."),
            NumberRange(min=0.0, max=10.0, message="Value must be between 0.0 and 10.0 mm.")
        ],
        default=0.5,
        description="ST depression induced by exercise relative to resting baseline."
    )
    st_slope = SelectField(
        'Slope of Peak Exercise ST Segment',
        choices=[
            ('0', 'Upsloping (Physiologically Normal)'),
            ('1', 'Flat (Horizontal / Potential Ischemia)'),
            ('2', 'Downsloping (Marked Ischemic Strain)')
        ],
        validators=[DataRequired()]
    )
    num_major_vessels = SelectField(
        'Major Vessels Colored by Fluoroscopy (0 - 3)',
        choices=[
            ('0', '0 Vessels (Clear patent coronary tree)'),
            ('1', '1 Major Vessel Occluded / Narrowed'),
            ('2', '2 Major Vessels Involved'),
            ('3', '3 Major Vessels (Multivessel Disease)')
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Run Cardiovascular Risk Inference')
