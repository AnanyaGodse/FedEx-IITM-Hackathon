from stable_baselines3 import DQN
from environment import RouteOptimizationEnv

def evaluate_dqn():
    # Load the trained model
    model = DQN.load("models/dqn_route_optimization_mumbai")

    # Initialize environment for Mumbai
    env = RouteOptimizationEnv()

    # Evaluate the model
    state = env.reset()
    done = False
    total_reward = 0

    while not done:
        action, _ = model.predict(state)
        state, reward, done, _ = env.step(action)
        total_reward += reward

    print(f"Total reward: {total_reward}")

if __name__ == "__main__":
    evaluate_dqn()

