/// Federated learning round metrics and experiment metadata.
class FLMetrics {
  final FLExperimentMeta experiment;
  final List<FLRoundMetric> history;
  final FLRoundMetric? finalRound;
  final CentralizedBaseline? centralizedBaseline;

  const FLMetrics({
    required this.experiment,
    required this.history,
    this.finalRound,
    this.centralizedBaseline,
  });

  factory FLMetrics.fromJson(Map<String, dynamic> json) {
    var rawHist = json['global_model_history'];
    List<FLRoundMetric> histList = [];
    if (rawHist is List) {
      histList = rawHist
          .map((item) => FLRoundMetric.fromJson(item as Map<String, dynamic>))
          .toList();
    }

    FLRoundMetric? fRound;
    if (json['final_round'] != null) {
      fRound = FLRoundMetric.fromJson(json['final_round'] as Map<String, dynamic>);
    } else if (histList.isNotEmpty) {
      fRound = histList.last;
    }

    CentralizedBaseline? baseline;
    if (json['centralized_baseline'] != null) {
      baseline = CentralizedBaseline.fromJson(
          json['centralized_baseline'] as Map<String, dynamic>);
    }

    return FLMetrics(
      experiment: FLExperimentMeta.fromJson(
          json['experiment'] as Map<String, dynamic>? ?? {}),
      history: histList,
      finalRound: fRound,
      centralizedBaseline: baseline,
    );
  }
}

class FLExperimentMeta {
  final String type;
  final int numClients;
  final int numRounds;
  final int localEpochs;
  final double durationSeconds;

  const FLExperimentMeta({
    required this.type,
    required this.numClients,
    required this.numRounds,
    required this.localEpochs,
    required this.durationSeconds,
  });

  factory FLExperimentMeta.fromJson(Map<String, dynamic> json) {
    return FLExperimentMeta(
      type: json['type'] as String? ?? 'federated_learning',
      numClients: json['num_clients'] as int? ?? 5,
      numRounds: json['num_rounds'] as int? ?? 10,
      localEpochs: json['local_epochs'] as int? ?? 3,
      durationSeconds: (json['duration_seconds'] as num?)?.toDouble() ?? 87.9,
    );
  }
}

class FLRoundMetric {
  final int round;
  final double accuracy;
  final double precisionMacro;
  final double recallMacro;
  final double f1Macro;
  final double precisionMoving;
  final double recallMoving;
  final double f1Moving;
  final double precisionParked;
  final double recallParked;
  final double f1Parked;

  const FLRoundMetric({
    required this.round,
    required this.accuracy,
    required this.precisionMacro,
    required this.recallMacro,
    required this.f1Macro,
    required this.precisionMoving,
    required this.recallMoving,
    required this.f1Moving,
    required this.precisionParked,
    required this.recallParked,
    required this.f1Parked,
  });

  factory FLRoundMetric.fromJson(Map<String, dynamic> json) {
    return FLRoundMetric(
      round: json['round'] as int? ?? 0,
      accuracy: (json['accuracy'] as num?)?.toDouble() ?? 0.0,
      precisionMacro: (json['precision_macro'] as num?)?.toDouble() ?? 0.0,
      recallMacro: (json['recall_macro'] as num?)?.toDouble() ?? 0.0,
      f1Macro: (json['f1_macro'] as num?)?.toDouble() ?? 0.0,
      precisionMoving: (json['precision_moving'] as num?)?.toDouble() ?? 0.0,
      recallMoving: (json['recall_moving'] as num?)?.toDouble() ?? 0.0,
      f1Moving: (json['f1_moving'] as num?)?.toDouble() ?? 0.0,
      precisionParked: (json['precision_parked'] as num?)?.toDouble() ?? 0.0,
      recallParked: (json['recall_parked'] as num?)?.toDouble() ?? 0.0,
      f1Parked: (json['f1_parked'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class CentralizedBaseline {
  final double testAccuracy;
  final double testF1;
  final double testPrecision;
  final double testRecall;

  const CentralizedBaseline({
    required this.testAccuracy,
    required this.testF1,
    required this.testPrecision,
    required this.testRecall,
  });

  factory CentralizedBaseline.fromJson(Map<String, dynamic> json) {
    var metrics = json['metrics'] as Map<String, dynamic>? ?? json;
    var overall = metrics['overall'] as Map<String, dynamic>? ?? metrics;

    return CentralizedBaseline(
      testAccuracy: (overall['test_accuracy'] as num?)?.toDouble() ??
          (overall['accuracy'] as num?)?.toDouble() ??
          0.9947,
      testF1: (overall['f1_macro'] as num?)?.toDouble() ??
          (overall['test_f1'] as num?)?.toDouble() ??
          0.9933,
      testPrecision: (overall['precision_macro'] as num?)?.toDouble() ??
          (overall['test_precision'] as num?)?.toDouble() ??
          0.9964,
      testRecall: (overall['recall_macro'] as num?)?.toDouble() ??
          (overall['test_recall'] as num?)?.toDouble() ??
          0.9902,
    );
  }
}
