
# package import
from tensorflow.python.framework import dtypes
from tensorflow_io.bigquery import BigQueryClient
import tensorflow as tf
from google.cloud import bigquery
from google.cloud import aiplatform
import argparse
import os

# import argument to local variables
parser = argparse.ArgumentParser()
# the passed param, dest: a name for the param, default: if absent fetch this param from the OS, type: type to convert to, help: description of argument
parser.add_argument('--epochs', dest = 'epochs', default = 10, type = int, help = 'Number of Epochs')
parser.add_argument('--batch_size', dest = 'batch_size', default = 32, type = int, help = 'Batch Size')
parser.add_argument('--var_target', dest = 'var_target', type=str)
parser.add_argument('--var_omit', dest = 'var_omit', type=str)#, nargs='*')
parser.add_argument('--project_id', dest = 'project_id', type=str)
parser.add_argument('--bq_project', dest = 'bq_project', type=str)
parser.add_argument('--bq_dataset', dest = 'bq_dataset', type=str)
parser.add_argument('--bq_table', dest = 'bq_table', type=str)
parser.add_argument('--region', dest = 'region', type=str)
parser.add_argument('--experiment', dest = 'experiment', type=str)
parser.add_argument('--series', dest = 'series', type=str)
parser.add_argument('--experiment_name', dest = 'experiment_name', type=str)
parser.add_argument('--run_name', dest = 'run_name', type=str)
args = parser.parse_args()

# clients
bq = bigquery.Client(project = args.project_id)
aiplatform.init(project = args.project_id, location = args.region)

# Vertex AI Experiment
if args.run_name in [run.name for run in aiplatform.ExperimentRun.list(experiment = args.experiment_name)]:
    expRun = aiplatform.ExperimentRun(run_name = args.run_name, experiment = args.experiment_name)
else:
    expRun = aiplatform.ExperimentRun.create(run_name = args.run_name, experiment = args.experiment_name)
expRun.log_params({'experiment': args.experiment, 'series': args.series, 'project_id': args.project_id})

# get schema from bigquery source
query = f"SELECT * FROM {args.bq_project}.{args.bq_dataset}.INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{args.bq_table}'"
schema = bq.query(query).to_dataframe()

# get number of classes from bigquery source
nclasses = bq.query(query = f'SELECT DISTINCT {args.var_target} FROM {args.bq_project}.{args.bq_dataset}.{args.bq_table} WHERE {args.var_target} is not null').to_dataframe()
nclasses = nclasses.shape[0]
expRun.log_params({'data_source': f'bq://{args.bq_project}.{args.bq_dataset}.{args.bq_table}', 'nclasses': nclasses, 'var_split': 'splits', 'var_target': args.var_target})

# Make a list of columns to omit
OMIT = [x for x in args.var_omit.split(',') if x != '']

# use schema to prepare a list of columns to read from BigQuery
selected_fields = schema[~schema.column_name.isin(OMIT)].column_name.tolist()

# all the columns in this data source are either float64 or int64
output_types = [dtypes.float64 if x=='FLOAT64' else dtypes.int64 for x in schema[~schema.column_name.isin(OMIT)].data_type.tolist()]

# remap input data to Tensorflow inputs of features and target
def transTable(row_dict):
    target = row_dict.pop(args.var_target)
    target = tf.one_hot(tf.cast(target, tf.int64), nclasses)
    target = tf.cast(target, tf.float32)
    return(row_dict, target)

# function to setup a bigquery reader with Tensorflow I/O
def bq_reader(split):
    reader = BigQueryClient()

    training = reader.read_session(
        parent = f"projects/{args.project_id}",
        project_id = args.bq_project,
        table_id = args.bq_table,
        dataset_id = args.bq_dataset,
        selected_fields = selected_fields,
        output_types = output_types,
        row_restriction = f"splits='{split}'",
        requested_streams = 3
    )
    
    return training

# setup feed for train, validate and test
train = bq_reader('TRAIN').parallel_read_rows().prefetch(1).map(transTable).shuffle(args.batch_size*10).batch(args.batch_size)
validate = bq_reader('VALIDATE').parallel_read_rows().prefetch(1).map(transTable).batch(args.batch_size)
test = bq_reader('TEST').parallel_read_rows().prefetch(1).map(transTable).batch(args.batch_size)
expRun.log_params({'training.batch_size': args.batch_size, 'training.shuffle': 10*args.batch_size, 'training.prefetch': 1})
# Logistic Regression

# feature list
numeric_features = [feature for feature in schema[~schema.column_name.isin(OMIT + [args.var_target])]['column_name'].to_list()]

# feature inputs
features = [tf.keras.Input(shape = (1,), dtype = dtypes.float64, name = feature) for feature in numeric_features]

# normalize features - before training
#normalized_features = []
#for feature in features:
#    normalizer = tf.keras.layers.Normalization(axis = None, name = feature.name + '_normalized')
#    feature_data = train.map(lambda x, y: x[feature.name])
#    normalizer.adapt(feature_data)
#    normalized_features.append(normalizer(feature))

# concatenate features
all_features = tf.keras.layers.Concatenate(name = 'feature_layer')(features)
#all_features = tf.keras.layers.Concatenate(name = 'feature_layer')(normalized_features) # (features)

# batch normalization of inputs - during training
all_features = tf.keras.layers.BatchNormalization(name = 'batch_normalization_layer')(all_features)

# logistic - using softmax activation to nclasses
logistic = tf.keras.layers.Dense(nclasses, activation = tf.nn.softmax, name = 'logistic')(all_features)

# the model
model = tf.keras.Model(
    inputs = features,
    outputs = logistic,
    name = args.experiment
)

# compile the model
model.compile(
    optimizer = tf.keras.optimizers.SGD(), #SGD or Adam
    loss = tf.keras.losses.CategoricalCrossentropy(),
    metrics = ['accuracy', tf.keras.metrics.AUC(curve = 'PR', name = 'auprc')]
)

# setup tensorboard logs and train
tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=os.environ['AIP_TENSORBOARD_LOG_DIR'], histogram_freq=1)
history = model.fit(train, epochs = args.epochs, callbacks = [tensorboard_callback], validation_data = validate)
expRun.log_params({'training.epochs': history.params['epochs']})
for e in range(0, history.params['epochs']):
    expRun.log_time_series_metrics(
        {
            'train_loss': history.history['loss'][e],
            'train_accuracy': history.history['accuracy'][e],
            'train_auprc': history.history['auprc'][e],
            'val_loss': history.history['val_loss'][e],
            'val_accuracy': history.history['val_accuracy'][e],
            'val_auprc': history.history['val_auprc'][e]
        }
    )

# test evaluations:
loss, accuracy, auprc = model.evaluate(test)
expRun.log_metrics({'test_loss': loss, 'test_accuracy': accuracy, 'test_auprc': auprc})

# val evaluations:
loss, accuracy, auprc = model.evaluate(validate)
expRun.log_metrics({'val_loss': loss, 'val_accuracy': accuracy, 'val_auprc': auprc})

# training evaluations:
loss, accuracy, auprc = model.evaluate(train)
expRun.log_metrics({'train_loss': loss, 'train_accuracy': accuracy, 'train_auprc': auprc})

# output the model save files
model.save(os.getenv("AIP_MODEL_DIR"))
expRun.log_params({'model.save': os.getenv("AIP_MODEL_DIR")})
expRun.end_run()
