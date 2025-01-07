from stable_baselines3 import DQN
from environment import RouteOptimizationEnv

def train_dqn():
    # Initialize environment for Mumbai
    env = RouteOptimizationEnv()

    # Define the model (DQN)
    model = DQN(
        "MlpPolicy",  # Policy type (how the agent decides which action to take)
        env,
        learning_rate=1e-3,
        buffer_size=50000,
        learning_starts=1000,
        batch_size=32,
        gamma=0.99,
        verbose=1
    )

    # Train the model
    model.learn(total_timesteps=10000)  # Train for a certain number of time steps

    # Save the trained model
    model.save("models/dqn_route_optimization_mumbai")

if __name__ == "__main__":
    train_dqn()


