import distopia
from distopia.app.agent import VoronoiAgent

if __name__=='__main__':
    import time
    import random
    agent = VoronoiAgent()
    agent.load_data()
    print('data loaded')

    w, h = agent.screen_size
    t = [0, ] * 10
    for i in range(len(t)):
        ts = time.clock()
        fids = {i: [(random.random() * w, random.random() * h)] for i in range(4)}
        print(fids)
        try:
            state_v,district_v = agent.compute_voronoi_metrics(fids)
            for d in district_v:
                print("District {}:\n".format(d))
                for stat in district_v[d]:
                    print("\t{}\n".format(stat.get_data()))
        except Exception:
            print("Couldn't compute Vornoi for {}".format(fids))
            raise
        t[i] = time.clock() - ts
    print('done in {} - {}'.format(min(t), max(t)))