"""
Generate realistic heat exchanger (échangeur) sensor data for testing.

This script creates synthetic data based on thermodynamic principles:
- Heat transfer between hot and cold fluids
- Fouling degradation over time
- Internal leak detection patterns
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta


class HeatExchangerSimulator:
    """Simulate realistic heat exchanger behavior with defects."""
    
    def __init__(self, n_samples=500):
        self.n_samples = n_samples
        self.timestamps = [
            (datetime(2025, 1, 1) + timedelta(minutes=i)).isoformat()
            for i in range(n_samples)
        ]
        
    def normal_operation(self):
        """Generate normal operation data."""
        # Hot side: inlet 80°C → outlet 45°C
        temp_in_hot = 80 + np.random.normal(0, 2, self.n_samples)
        temp_out_hot = 45 + np.random.normal(0, 1.5, self.n_samples)
        
        # Cold side: inlet 15°C → outlet 35°C
        temp_in_cold = 15 + np.random.normal(0, 1, self.n_samples)
        temp_out_cold = 35 + np.random.normal(0, 1.5, self.n_samples)
        
        # Flow rate: 100 L/min
        flow_rate = 100 + np.random.normal(0, 5, self.n_samples)
        
        return pd.DataFrame({
            'timestamp': self.timestamps,
            'temp_in_hot': temp_in_hot,
            'temp_out_hot': temp_out_hot,
            'temp_in_cold': temp_in_cold,
            'temp_out_cold': temp_out_cold,
            'flow_rate': flow_rate,
        })
    
    def fouling_progressive(self):
        """Generate progressive fouling (encrassement) pattern."""
        df = self.normal_operation()
        
        # Fouling reduces heat transfer efficiency over time
        # Hot outlet temperature increases (less heat transferred)
        fouling_factor = np.linspace(0, 8, self.n_samples)
        df['temp_out_hot'] += fouling_factor
        
        # Cold outlet temperature decreases (receives less heat)
        df['temp_out_cold'] -= fouling_factor * 0.8
        
        return df
    
    def internal_leak(self):
        """Generate internal leak (fuite) pattern."""
        df = self.normal_operation()
        
        # Leak causes mixing between hot and cold streams
        # Hot side loses temperature faster
        leak_effect = np.random.uniform(0, 5, self.n_samples)
        df['temp_out_hot'] -= leak_effect
        
        # Cold side gains temperature abnormally
        df['temp_out_cold'] += leak_effect * 0.7
        
        # Flow rate instability
        df['flow_rate'] += np.random.normal(0, 10, self.n_samples)
        
        return df
    
    def mixed_dataset(self, normal_ratio=0.7, fouling_ratio=0.2, leak_ratio=0.1):
        """Generate mixed dataset with all patterns."""
        n_normal = int(self.n_samples * normal_ratio)
        n_fouling = int(self.n_samples * fouling_ratio)
        n_leak = self.n_samples - n_normal - n_fouling
        
        # Generate each pattern
        sim_normal = HeatExchangerSimulator(n_normal)
        df_normal = sim_normal.normal_operation()
        df_normal['label'] = 'normal_operation'
        
        sim_fouling = HeatExchangerSimulator(n_fouling)
        df_fouling = sim_fouling.fouling_progressive()
        df_fouling['label'] = 'encrassement_progressif'
        
        sim_leak = HeatExchangerSimulator(n_leak)
        df_leak = sim_leak.internal_leak()
        df_leak['label'] = 'fuite_interne'
        
        # Combine and shuffle
        df_combined = pd.concat([df_normal, df_fouling, df_leak], ignore_index=True)
        df_combined = df_combined.sample(frac=1).reset_index(drop=True)
        
        # Update timestamps to be sequential
        df_combined['timestamp'] = [
            (datetime(2025, 1, 1) + timedelta(minutes=i)).isoformat()
            for i in range(len(df_combined))
        ]
        
        return df_combined


def main():
    """Generate and save heat exchanger data."""
    print("🔥 Generating Heat Exchanger Data...")
    
    # Create simulator
    simulator = HeatExchangerSimulator(n_samples=500)
    
    # Generate mixed dataset
    df = simulator.mixed_dataset(
        normal_ratio=0.70,    # 70% normal
        fouling_ratio=0.20,   # 20% fouling
        leak_ratio=0.10       # 10% leak
    )
    
    # Save CSV for IoT replay
    output_path = Path(__file__).parent.parent / 'iot' / 'data' / 'echangeur.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove label column for production CSV
    df_production = df.drop(columns=['label'])
    df_production.to_csv(output_path, index=False, float_format='%.4f')
    
    # Save labeled dataset for training
    training_path = output_path.parent / 'echangeur_labeled.csv'
    df.to_csv(training_path, index=False, float_format='%.4f')
    
    print(f"✅ Production CSV saved: {output_path}")
    print(f"✅ Training CSV saved: {training_path}")
    
    # Statistics
    print(f"\n📊 Dataset Statistics:")
    print(f"  Total samples: {len(df)}")
    print(f"  Normal: {len(df[df['label'] == 'normal_operation'])}")
    print(f"  Fouling: {len(df[df['label'] == 'encrassement_progressif'])}")
    print(f"  Leak: {len(df[df['label'] == 'fuite_interne'])}")
    print(f"\n🌡️ Temperature Ranges:")
    print(f"  Hot inlet: {df['temp_in_hot'].min():.2f} - {df['temp_in_hot'].max():.2f} °C")
    print(f"  Hot outlet: {df['temp_out_hot'].min():.2f} - {df['temp_out_hot'].max():.2f} °C")
    print(f"  Cold inlet: {df['temp_in_cold'].min():.2f} - {df['temp_in_cold'].max():.2f} °C")
    print(f"  Cold outlet: {df['temp_out_cold'].min():.2f} - {df['temp_out_cold'].max():.2f} °C")
    print(f"  Flow rate: {df['flow_rate'].min():.2f} - {df['flow_rate'].max():.2f} L/min")


if __name__ == '__main__':
    main()
