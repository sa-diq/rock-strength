

def get_plot_characteristics():
    # Prompt user to enter the name of the plot
    plot_name = input("Enter the name of the plot(Author(s)_Year_FigureNumber): ") # Note: we can decide collect the author(s), year, and figure number separately. Liase with Dave.
    # Prompt user for number of sandstones in the plot
    num_sandstones = int(input("Enter the number of sandstones in the plot: "))
    while num_sandstones <= 0:
        print("Please enter a positive integer.")
        num_sandstones = int(input("Enter the number of sandstones in the plot: "))

    sandstone_names = []
    for sandstone_index in range(num_sandstones):
        name = input(f"Enter the name of sandstone {sandstone_index + 1}: ")
        sandstone_names.append(name.strip().title())

    print(f"\nPlot name: {plot_name}")
    print(f"\nSandstone names: {sandstone_names}")