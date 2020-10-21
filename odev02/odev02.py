import sys
class Airline():
    def __init__(self, data):
        self.name = data[0]
        self.partners = []
        i = 1
        while i< len(data):
            self.partners.append(data[i])
            i = i+1
    
    def get_partners(self):
        return self.partners

    def is_partner(self, name):
        if name in self.partners:
            return True
        else:
            return False

    def get_name(self):
        return self.name


def main():
    airlines_partners_network = []

    try:
        with open("airlines.txt", "r") as f:
            for line in f:
                airline_list = []
                current_line = line.split(',')
                for airline in current_line:
                    airline = airline.replace('\n', '')
                    airline_list.append(airline)
                new_airline = Airline(airline_list)
                airlines_partners_network.append(new_airline)
    except:
        print('Error reading file...')

    def check_airlines():
        airline_on = sys.argv[1]
        goal_airline = sys.argv[2]
        path_for_miles = []
        airlines_visited = []
        if can_redeem(airline_on, goal_airline, path_for_miles, airlines_visited, airlines_partners_network) is True:
            print("Path to redeem miles: " + str(path_for_miles))
        else:
            print("Can not convert miles from " + airline_on  +" to " + goal_airline +".")
    def can_redeem(current, goal, path_for_miles, airlines_visited, network):
        if current == goal:
            path_for_miles.append(current)
            return True
        elif current in airlines_visited:
            return False
        else:
            airlines_visited.append(current)
            path_for_miles.append(current)
            pos = -1
            index = 0
            while pos == -1 and index < len(network):
                if current == network[index].get_name():
                    pos = index
                index = index+1
            
            if pos == -1:
                return False

            found_path = False
            index = 0
            partners = network[pos].get_partners()
            while found_path is False and index < len(partners):
                found_path = can_redeem(partners[index], goal, path_for_miles, airlines_visited, network)
                index = index +1
            if found_path is False:
                path_for_miles.pop(len(path_for_miles) -1)
            return found_path
    check_airlines()

if __name__ == '__main__':
    main()