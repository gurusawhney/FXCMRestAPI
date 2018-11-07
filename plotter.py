import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

if __name__ == "__main__":
    """
    A simple script to plot the balance of the portfolio, or
    "equity curve", as a function of time.
    """
    sns.set_palette("deep", desat=.6)
    sns.set_context(rc={"figure.figsize": (8, 4)})
    equity_file = open("equity.csv")
    equity = pd.io.parsers.read_csv(
        equity_file, parse_dates=True, header=0, index_col=0
    )
    # Plot three charts: Equity curve, period returns, drawdowns
    fig = plt.figure()
    fig.patch.set_facecolor('white')  # Set the outer colour to white
    # Plot the equity curve
    ax1 = fig.add_subplot(311, ylabel='Portfolio value')
    equity["Equity"].plot(ax=ax1, color=sns.color_palette()[0])
    # Plot the returns
    ax2 = fig.add_subplot(312, ylabel='Period returns')
    equity['Returns'].plot(ax=ax2, color=sns.color_palette()[1])
    # Plot the returns
    ax3 = fig.add_subplot(313, ylabel='Drawdowns')
    equity['Drawdown'].plot(ax=ax3, color=sns.color_palette()[2])
    # Plot the figure
    fig.subplots_adjust(hspace=1)
    plt.show()