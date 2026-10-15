import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/theme/app_colors.dart';
import '../core/theme/app_typography.dart';
import '../models/vehicle_reading.dart';
import '../providers/parking_provider.dart';

/// Modal bottom sheet enabling telemetry simulation & live ML state inference.
class VehicleSimulatorSheet extends StatefulWidget {
  const VehicleSimulatorSheet({super.key});

  @override
  State<VehicleSimulatorSheet> createState() => _VehicleSimulatorSheetState();
}

class _VehicleSimulatorSheetState extends State<VehicleSimulatorSheet> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _idController;
  late TextEditingController _latController;
  late TextEditingController _lonController;
  late TextEditingController _speedController;
  late TextEditingController _rssiController;
  VehicleReading? _latestResult;

  @override
  void initState() {
    super.initState();
    final randomId = 'VH_${1000 + math.Random().nextInt(9000)}';
    _idController = TextEditingController(text: randomId);
    _latController = TextEditingController(text: '18.5204');
    _lonController = TextEditingController(text: '73.8567');
    _speedController = TextEditingController(text: '0.0');
    _rssiController = TextEditingController(text: '-52.0');
  }

  @override
  void dispose() {
    _idController.dispose();
    _latController.dispose();
    _lonController.dispose();
    _speedController.dispose();
    _rssiController.dispose();
    super.dispose();
  }

  void _applyPreset(String name) {
    if (name == 'parked') {
      _speedController.text = '0.0';
      _rssiController.text = '-48.0';
      _latController.text = '18.5205';
      _lonController.text = '73.8565';
    } else {
      _speedController.text = '8.5';
      _rssiController.text = '-88.0';
      _latController.text = '18.5215';
      _lonController.text = '73.8552';
    }
    setState(() {});
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final reading = VehicleReading(
      vehicleId: _idController.text.trim(),
      timestamp: DateTime.now(),
      lat: double.parse(_latController.text.trim()),
      lon: double.parse(_lonController.text.trim()),
      gpsSpeed: double.tryParse(_speedController.text.trim()),
      bleRssi: double.tryParse(_rssiController.text.trim()),
      predictedState: 'moving',
    );
    final result = await context.read<ParkingProvider>().submitTelemetry(reading);
    if (mounted) setState(() => _latestResult = result);
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ParkingProvider>();
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppColors.surfaceBorder,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('Telemetry Simulator', style: AppTypography.titleLarge),
                  IconButton(
                    icon: const Icon(Icons.close_rounded, size: 20),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  ActionChip(
                    label: const Text('Parked (Zero V)', style: TextStyle(fontSize: 11)),
                    backgroundColor: AppColors.surfaceElevated,
                    onPressed: () => _applyPreset('parked'),
                  ),
                  const SizedBox(width: 8),
                  ActionChip(
                    label: const Text('Cruising (High V)', style: TextStyle(fontSize: 11)),
                    backgroundColor: AppColors.surfaceElevated,
                    onPressed: () => _applyPreset('moving'),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              TextFormField(
                controller: _idController,
                decoration: inputDec('Vehicle ID', Icons.badge_rounded),
                validator: (v) => v!.isEmpty ? 'Enter ID' : null,
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _latController,
                      keyboardType: TextInputType.number,
                      decoration: inputDec('Latitude', Icons.location_on_rounded),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: TextFormField(
                      controller: _lonController,
                      keyboardType: TextInputType.number,
                      decoration: inputDec('Longitude', Icons.location_on_rounded),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _speedController,
                      keyboardType: TextInputType.number,
                      decoration: inputDec('Speed m/s', Icons.speed_rounded),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: TextFormField(
                      controller: _rssiController,
                      keyboardType: TextInputType.number,
                      decoration: inputDec('BLE RSSI', Icons.bluetooth_rounded),
                    ),
                  ),
                ],
              ),
              if (_latestResult != null) ...[
                const SizedBox(height: 14),
                buildResultBadge(_latestResult!),
              ],
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: provider.isSubmittingTelemetry ? null : _submit,
                  icon: provider.isSubmittingTelemetry
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.send_rounded, size: 18),
                  label: Text(provider.isSubmittingTelemetry
                      ? 'Informing ML Model...'
                      : 'Send & Classify State'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

Widget buildResultBadge(VehicleReading r) {
    final color = r.isParked ? AppColors.stateParked : AppColors.stateMoving;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withAlpha(25),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withAlpha(90)),
      ),
      child: Row(
        children: [
          Icon(
            r.isParked ? Icons.local_parking_rounded : Icons.directions_car_rounded,
            color: color,
            size: 24,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'ML Inferred State: ${r.predictedState.toUpperCase()}',
                  style: TextStyle(
                    color: color,
                    fontWeight: FontWeight.w700,
                    fontSize: 13,
                  ),
                ),
                Text(
                  'Zone: ${r.zoneId ?? "Outside Grid"} • Conf: ${((r.confidence ?? 0.99) * 100).toStringAsFixed(1)}%',
                  style: AppTypography.labelSmall,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  InputDecoration inputDec(String label, IconData icon) {
    return InputDecoration(
      labelText: label,
      labelStyle: const TextStyle(color: AppColors.textMuted, fontSize: 12),
      prefixIcon: Icon(icon, size: 16, color: AppColors.textMuted),
      filled: true,
      fillColor: AppColors.surfaceElevated,
      contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: const BorderSide(color: AppColors.surfaceBorder),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: const BorderSide(color: AppColors.surfaceBorder),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: const BorderSide(color: AppColors.primary),
      ),
    );
  }
}

